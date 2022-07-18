
import argparse
import json
import pathlib
import time

from backend.config import data_filepath, backend_http_port, time_stack_naming, time_stack_max_depth
from backend.http_core import MyServer, load_file

def now():
    return int(time.time() * 1000 * 1000 * 1000)  # in nano-second


class TTSM:

    def __init__(self, db_filepath):

        self.tasks_pool = [{
            'task_id': 0,
            'parent_task_id': -1,
            'task_name': 'root_task',
        }]
        self.sub_tasks = {0: []}
        self.time_stack = [{
            'full_name': 'root',
            'short_name': 'root',
            'state': 2,
            'child_counter': 0,
            'timestamp_1': 0,  # FIXME
            'timestamp_2': 0,  # FIXME
        }]
        self.popped_time_slots = []
        self.task_assigned_depth = [time_stack_max_depth]

        if not pathlib.Path(db_filepath).exists():
            db_file_init = open(db_filepath, 'x', encoding='utf8')
            # db_file_init.write()  # TODO  write some initial commands ??
            db_file_init.close()
            print('Created new database "\033[1;34m{}\033[0m".'.format(db_filepath))

        db_file_read = open(db_filepath, 'r', encoding='utf8')
        for command_str in db_file_read.readlines():  # One command per line.
            command = json.loads(command_str)
            self.execute(command, True)
        db_file_read.close()

        self.db_file_append = open(db_filepath, 'a', encoding='utf8')
        self.closed = False

    def close(self):
        self.db_file_append.close()
        self.closed = True

    def execute(self, command, loaded_from_db=False):
        if not loaded_from_db:
            command['timestamp'] = now()
            if not self.closed:
                command_str = json.dumps(command)
                self.db_file_append.write(command_str+'\n')
                self.db_file_append.flush()
            else:
                raise Exception('System already closed!')

        if command['name'] == 'task_add':
            new_task_id = len(self.tasks_pool)
            command['new_task']['task_id'] = new_task_id

            parent_task_id = command['new_task']['parent_task_id']
            if parent_task_id >= new_task_id:
                return {'success': False, 'reason': 'Parent task #{} not exists.'.format(parent_task_id)}

            self.tasks_pool.append(command['new_task'])
            self.sub_tasks[new_task_id] = []
            self.sub_tasks[parent_task_id].append(new_task_id)

            if 'suggested_assigned_depth' in command:
                self.task_assigned_depth.append(command['suggested_assigned_depth'])
            else:
                self.task_assigned_depth.append(0)

            # new_task_assigned_depth = command['assigned_depth'] if ('assigned_depth' in command) else 0
            # self.task_assigned_depth.append(0)  # should give a guaranteed-valid depth, so assign() can start traversing along parent tasks.
            # self.assign(new_task_id, new_task_assigned_depth)

            # self.task_assigned_depth.append(self.task_assigned_depth[parent_task_id])
            # Note: Modification on these server codes may lead to strange results and inaccurate history.

            return {'success': True, 'current_tasks_pool': self.tasks_pool, 'current_sub_tasks': self.sub_tasks, 'current_task_assigned_depth': self.task_assigned_depth}

        elif command['name'] == 'task_modify':
            task_id = command['new_task']['task_id']
            if task_id == 0:
                return {'success': False, 'reason': 'Root task cannot be modified.'}
            if task_id < 0 or task_id >= len(self.tasks_pool):
                return {'success': False, 'reason': 'Task #{} not exists.'.format(task_id)}

            old_parent_task_id = self.tasks_pool[task_id]['parent_task_id']
            new_parent_task_id = command['new_task']['parent_task_id']
            if new_parent_task_id < 0 or new_parent_task_id >= len(self.tasks_pool):
                return {'success': False, 'reason': 'Task #{} (modified parent task) not exists.'.format(new_parent_task_id)}
            if new_parent_task_id == task_id:
                return {'success': False, 'reason': 'Task #{} \'s parent task should not be itself.'.format(new_parent_task_id)}
            # TODO  avoid parent loop

            self.tasks_pool[task_id] = command['new_task']
            if old_parent_task_id != new_parent_task_id:
                self.sub_tasks[old_parent_task_id].remove(task_id)
                self.sub_tasks[new_parent_task_id].append(task_id)
                if self.task_assigned_depth[new_parent_task_id] < self.task_assigned_depth[task_id]:
                    self.assign(new_parent_task_id, self.task_assigned_depth[task_id])  # FIXME  may not be in STARTING state.

            return {'success': True, 'current_tasks_pool': self.tasks_pool, 'current_sub_tasks': self.sub_tasks, 'current_task_assigned_depth': self.task_assigned_depth}

        # elif command['name'] == 'task_modify_detail':
        #     task_id = command['task_id']
        #     if task_id == 0:
        #         return {'success': False, 'reason': 'Root task cannot be modified.'}
        #     if task_id < 0 or task_id >= len(self.tasks_pool):
        #         return {'success': False, 'reason': 'Task #{} not exists.'.format(task_id)}
        #
        #     key = command['key']
        #     old_value = self.tasks_pool[task_id][key] if (key in self.tasks_pool[task_id]) else None
        #     new_value = command['new_value']
        #     if key == 'task_id':
        #         return {'success': False, 'reason': 'Key "task_id" cannot be modified.'}
        #
        #     self.tasks_pool[task_id][key] = new_value
        #     if key == 'parent_task_id':
        #         self.sub_tasks[old_value].remove(task_id)
        #         self.sub_tasks[new_value].append(task_id)
        #         # FIXME  also update task_assigned_depth
        #
        #     return {'success': True, 'current_tasks_pool': self.tasks_pool, 'current_sub_tasks': self.sub_tasks, 'current_task_assigned_depth': self.task_assigned_depth}

        elif command['name'] == 'time_stack_push':
            if self.time_stack[-1]['state'] != 2:
                return {'success': False, 'reason': 'Current time slot is NOT in RUNNING state.'}
            if len(self.time_stack) == len(time_stack_naming):
                return {'success': False, 'reason': 'Current time slot is of minimum level.'}

            self.time_stack[-1]['child_counter'] += 1
            current_time_slot_full_name = self.time_stack[-1]['full_name']
            new_time_slot_short_name = '{}{}'.format(self.time_stack[-1]['child_counter'], time_stack_naming[len(self.time_stack)])

            self.time_stack.append({
                'full_name': current_time_slot_full_name + new_time_slot_short_name,
                'short_name': new_time_slot_short_name,
                'state': 1,
                'child_counter': 0,
                'timestamp_1': command['timestamp']
            })
            return {'success': True, 'current_time_stack': self.time_stack}

        elif command['name'] == 'time_slot_start':
            if self.time_stack[-1]['state'] != 1:
                return {'success': False, 'reason': 'Current time slot is NOT in PREPARING state.'}

            self.time_stack[-1]['state'] = 2
            self.time_stack[-1]['timestamp_2'] = command['timestamp']
            return {'success': True, 'current_time_stack': self.time_stack}

        elif command['name'] == 'time_slot_stop':
            if self.time_stack[-1]['state'] != 2:
                return {'success': False, 'reason': 'Current time slot is NOT in RUNNING state.'}
            if len(self.time_stack) == 1:
                return {'success': False, 'reason': 'Current time slot is of root level.'}

            self.time_stack[-1]['state'] = 3
            self.time_stack[-1]['timestamp_3'] = command['timestamp']
            return {'success': True, 'current_time_stack': self.time_stack}

        elif command['name'] == 'time_stack_pop':
            if self.time_stack[-1]['state'] != 3:
                return {'success': False, 'reason': 'Current time slot is NOT in ENDING state.'}

            self.time_stack[-1]['state'] = 4
            self.time_stack[-1]['timestamp_4'] = command['timestamp']
            self.time_stack[-1]['evaluation'] = command['time_slot_evaluation']
            popped = self.time_stack.pop()
            self.popped_time_slots.append(popped)
            return {'success': True, 'current_time_stack': self.time_stack}

        elif command['name'] == 'assign':
            # if self.time_stack[-1]['state'] != 1:
            #     return {'success': False, 'reason': 'Current time slot is NOT in PREPARING state.'}

            # task_id = command['task_id']
            # depth = command['depth']
            # to_assign = command['to_assign']
            #
            # if to_assign:
            #     depth = new_depth
            #     while True:
            #
            # self.task_assigned_depth[task_id]

            return self.assign(command['task_id'], command['new_depth'])

        elif command['name'] == 'assign_subtree_at_least':
            # if self.time_stack[-1]['state'] != 1:
            #     return {'success': False, 'reason': 'Current time slot is NOT in PREPARING state.'}

            task_id = command['root_task_id']
            at_least_depth = command['at_least_depth']
            including_task_assigned_to_lower_depth = command['including_task_assigned_to_lower_depth'] if ('including_task_assigned_to_lower_depth' in command) else True
            # if task_id == 0:
            #     return {'success': False, 'reason': 'Assignment depth of root task cannot be modified.'}
            if task_id < 0 or task_id >= len(self.tasks_pool):
                return {'success': False, 'reason': 'Task #{} not exists.'.format(task_id)}
            if at_least_depth < 0 or at_least_depth > time_stack_max_depth:
                return {'success': False, 'reason': 'Time stack depth {} is not valid.'.format(at_least_depth)}

            modified_tasks = []
            queue = [task_id]
            while len(queue) > 0:
                task_id = queue[0]
                if (self.task_assigned_depth[task_id] < at_least_depth - 1) and not including_task_assigned_to_lower_depth:
                    queue = queue[1:]
                    continue
                if self.task_assigned_depth[task_id] < at_least_depth:
                    self.task_assigned_depth[task_id] = at_least_depth
                    modified_tasks.append(task_id)
                queue = queue[1:] + self.sub_tasks[task_id]

            return {'success': True, 'current_task_assigned_depth': self.task_assigned_depth, 'modified_tasks': modified_tasks}

        elif command['name'] == 'progress_report':
            pass  # TODO

        else:
            return {'success': False, 'msg': 'Unrecognized command "{}".'.format(command['name'])}

    def assign(self, task_id, new_depth):
        if task_id == 0:
            return {'success': False, 'reason': 'Assignment depth of root task cannot be modified.'}
        if task_id < 0 or task_id >= len(self.tasks_pool):
            return {'success': False, 'reason': 'Task #{} not exists.'.format(task_id)}
        if new_depth < 0 or new_depth > time_stack_max_depth:
            return {'success': False, 'reason': 'Time stack depth {} is not valid.'.format(new_depth)}

        modified_tasks = []

        # If assigning a task to a time slot of larger depth, the parent tasks should also be assigned to at least that depth.
        if new_depth > self.task_assigned_depth[task_id]:
            while task_id > 0 and new_depth > self.task_assigned_depth[task_id]:
                self.task_assigned_depth[task_id] = new_depth
                modified_tasks.append(task_id)
                task_id = self.tasks_pool[task_id]['parent_task_id']

        # If assigning a task to a time slot of smaller depth, the sub-tasks should also be assigned to at most that depth.
        elif new_depth < self.task_assigned_depth[task_id]:
            queue = [task_id]
            while len(queue) > 0:
                task_id = queue[0]
                if new_depth < self.task_assigned_depth[task_id]:
                    self.task_assigned_depth[task_id] = new_depth
                    modified_tasks.append(task_id)
                    queue = queue[1:] + self.sub_tasks[task_id]
                else:
                    queue = queue[1:]

        else:
            pass

        # tasks_tree_views = []  # For convenience of front-end to render the tree.
        # for depth in range(1, time_stack_max_depth):

        return {'success': True, 'current_task_assigned_depth': self.task_assigned_depth, 'modified_tasks': modified_tasks}


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=backend_http_port, help='the port to be listened on.')
    args_map = parser.parse_args()

    server = MyServer(args_map.port)
    ttsm = TTSM(data_filepath)


    def root_test(req_path, req_HTTP_payload):
        return req_path == '/'

    def root_action(req_path, req_HTTP_payload):
        return 'text/html', load_file('../frontend/index.html')

    server.register(root_test, root_action)


    def bundle_test(req_path, req_HTTP_payload):
        return req_path == '/index_bundle.js'

    def bundle_action(req_path, req_HTTP_payload):
        return 'application/javascript', load_file('../frontend/index_bundle.js')

    server.register(bundle_test, bundle_action)


    def execute_test(req_path, req_HTTP_payload):
        return req_path == '/execute'

    def execute_action(req_path, req_HTTP_payload):
        command = json.loads(req_HTTP_payload)
        if command['name'] == 'get_tasks':
            return 'application/json', json.dumps({'success': True, 'current_tasks_pool': ttsm.tasks_pool, 'current_sub_tasks': ttsm.sub_tasks})
        if command['name'] == 'get_time_stack':
            return 'application/json', json.dumps({'success': True, 'current_time_stack': ttsm.time_stack, 'time_stack_naming':time_stack_naming})
        if command['name'] == 'get_assignment':
            return 'application/json', json.dumps({'success': True, 'current_task_assigned_depth': ttsm.task_assigned_depth})
        return 'application/json', json.dumps(ttsm.execute(command))

    server.register(execute_test, execute_action)


    server.run()
    ttsm.close()
