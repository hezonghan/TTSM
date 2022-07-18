<template>
    <div class="sub_tree">
        <div
            class="current_task_info" 
            :style=" 
                ( ('hidden' in global_data.tasks_pool[current_task_id]) && global_data.tasks_pool[current_task_id].hidden ?
                    'background-color: lightgrey; color: black;' : 
                (global_data.task_assigned_depth[current_task_id] >= global_data.displaying_depth ? 
                    'background-color: cyan; color: black;' : 
                    'background-color: blue; color: yellow;'
                ))+';' "
            @contextmenu="open_main_menu(current_task_id)"
            @dblclick="change_assign(current_task_id)"
            >
            [#{{global_data.tasks_pool[current_task_id].task_id}}] {{global_data.tasks_pool[current_task_id].task_name}}
            <div class="task_comment" v-if=" 'comment' in global_data.tasks_pool[current_task_id] ">{{global_data.tasks_pool[current_task_id].comment}}</div>
        </div>
        <div>
            <span v-for="sub_task_id in global_data.sub_tasks[current_task_id]">
                <task_node 
                    v-if="(global_data.task_assigned_depth[sub_task_id] >= global_data.displaying_depth - 1) && !(
                            ('hidden' in global_data.tasks_pool[sub_task_id]) && 
                            global_data.tasks_pool[sub_task_id].hidden &&
                            (! global_data.show_hidden_tasks)
                        )"
                    :current_task_id="sub_task_id" :global_data="global_data"
                />
            </span>
        </div>
    </div>
    <div class="menu_wrapper">
        <div v-if="global_data.menu_task_id == current_task_id && global_data.menu_state == 0" class="menu">
            <div class="task_menu_button" @click="open_task_add_menu()">添加子任务</div>
            <div class="task_menu_button" @click="open_task_modify_menu()">修改任务</div>
            <div class="task_menu_button" @click="assign_subtree_at_least(false)">落实整个子树（仅上级已获任务）</div>
            <div class="task_menu_button" @click="assign_subtree_at_least(true)">落实整个子树（包括上级未获任务）</div>
            <div class="task_menu_button" @click="cancel_menu()">取消</div>
        </div>

        <div v-if="global_data.menu_task_id == current_task_id && (global_data.menu_state == 1 || global_data.menu_state == 2)" class="menu">
            <fieldset>
                <legend v-if="global_data.menu_state == 1">为任务#{{global_data.menu_task_id}}添加子任务</legend>
                <legend v-if="global_data.menu_state == 2">修改任务#{{global_data.menu_task_id}}</legend>

                <div>所属任务： #
                    <span v-if="global_data.menu_state == 1">{{global_data.menu_task_id}}</span>
                    <input v-if="global_data.menu_state == 2" v-model.number="input_task_parent_id" />
                </div>
                <div>任务名称：<input v-model="input_task_name" /></div>
                <div>备注：<textarea v-model="input_task_comment" /></div>
                <div><input type="checkbox" v-model="input_task_hidden" /> 隐藏任务</div>

                <div class="task_menu_button" @click="task_add_or_modify()">提交</div>
                <div class="task_menu_button" @click="cancel_menu()">取消</div>
            </fieldset>
        </div>

        <!-- <div v-if="global_data.menu_task_id == current_task_id && global_data.menu_state == 2" class="menu">
            <fieldset>
                <legend>修改任务#{{global_data.menu_task_id}}</legend>
                此功能暂未开放。
                <div class="task_menu_button" @click="cancel_menu()">取消</div>
            </fieldset>
        </div> -->

    </div>
</template>

<script>
    import axios from 'axios';

    export default {
        name: 'task_node',
        props: ['current_task_id', 'global_data'],  // 'tasks_pool', 'sub_tasks', 
        data() { return {
            input_task_parent_id: 0,
            input_task_name: '',
            input_task_comment: '',
            input_task_hidden: false,
        }},
        methods: {
            open_main_menu(current_task_id) {
                this.global_data.menu_task_id = current_task_id;
                this.global_data.menu_state = 0;
            },
            cancel_menu() {
                this.global_data.menu_task_id = -1;
                this.global_data.menu_state = -1;
            },
            open_task_add_menu() {
                this.global_data.menu_state = 1;

                // this.input_task_parent_id = -1;
                this.input_task_name = '';
                this.input_task_comment = '';
                this.input_task_hidden = '';
            },
            open_task_modify_menu() {
                this.global_data.menu_state = 2;

                this.input_task_parent_id = this.global_data.tasks_pool[this.global_data.menu_task_id].parent_task_id;
                this.input_task_name = this.global_data.tasks_pool[this.global_data.menu_task_id].task_name;
                this.input_task_comment = this.global_data.tasks_pool[this.global_data.menu_task_id].comment;
                this.input_task_hidden = this.global_data.tasks_pool[this.global_data.menu_task_id].hidden;
            },
            task_add_or_modify() {
                // var assigned_depth = this.global_data.displaying_depth - 1;
                // if(assigned_depth < 0) assigned_depth = 0;

                const that = this;
                // const menu_task_id = that.global_data.menu_task_id;  // for console.log only

                axios.post('/execute' , {
                    name: (this.global_data.menu_state == 1 ? 'task_add' : 'task_modify'),
                    new_task: {
                        task_id: (this.global_data.menu_state == 1 ? -1 : this.global_data.menu_task_id),  // if adding task, task_id is allocated by backend after submitted.
                        parent_task_id: (this.global_data.menu_state == 1 ? this.global_data.menu_task_id : this.input_task_parent_id),
                        task_name: this.input_task_name,
                        comment: this.input_task_comment,
                        hidden: this.input_task_hidden,
                    },
                    // assigned_depth: assigned_depth,
                    suggested_assigned_depth: (this.global_data.menu_state == 1 ? (this.global_data.displaying_depth == 0 ? 0 : this.global_data.displaying_depth - 1) : 'not-applicable'),
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.global_data.tasks_pool = response.data.current_tasks_pool;
                    that.global_data.sub_tasks = response.data.current_sub_tasks;
                    // console.log(that.global_data.tasks_pool[that.global_data.tasks_pool.length-1].task_id);
                    // console.log('parent #'+menu_task_id+' \'s sub_tasks: '+that.global_data.sub_tasks[menu_task_id]);
                    that.global_data.task_assigned_depth = response.data.current_task_assigned_depth;
                    // console.log(that.global_data.task_assigned_depth);
                });
                
                this.global_data.menu_task_id = -1;
                this.global_data.menu_state = -1;
            },
            change_assign(current_task_id) {
                var new_depth;
                if(this.global_data.task_assigned_depth[current_task_id] >= this.global_data.displaying_depth) {
                    if(this.global_data.displaying_depth == 0) {
                        alert('Cannot cancel assignment of a task from the root time slot.');
                        return;
                    }
                    new_depth = this.global_data.displaying_depth - 1;
                }else {
                    new_depth = this.global_data.displaying_depth;
                }
                
                const that = this;

                axios.post('/execute' , {
                    name: 'assign',
                    task_id: current_task_id,
                    new_depth: new_depth,
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.global_data.task_assigned_depth = response.data.current_task_assigned_depth;
                });
            },
            assign_subtree_at_least(including_task_assigned_to_lower_depth) {
                const that = this;

                axios.post('/execute' , {
                    name: 'assign_subtree_at_least',
                    root_task_id: this.global_data.menu_task_id,
                    at_least_depth: this.global_data.displaying_depth,
                    including_task_assigned_to_lower_depth: including_task_assigned_to_lower_depth,
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.global_data.task_assigned_depth = response.data.current_task_assigned_depth;
                });

                this.global_data.menu_task_id = -1;
                this.global_data.menu_state = -1;
            },
        }
    }
</script>

<style>
    .sub_tree {
        display: flex; flex-direction: row;
    }
    .current_task_info {
        border: black 1px solid;
        background-color: pink; padding: 5px; min-width: 50px;
    }
    .task_comment {
        color: grey;
        font-size: 12px;
        white-space: pre-wrap;
    }
    .menu_wrapper {
        width: 0px; height: 0px; padding: 0px;
    }
    .menu {
        position: relative; z-index: 1;
        left: 2px; width: 300px; min-height: 100px;
        padding: 5px;
        
        background-color: yellow;
        border: blue 1px solid;
    }
    .task_menu_button {
        padding: 5px; text-align: center;
        background-color: orange;
        margin-top: 10px;
    }
    .task_menu_button:hover {font-weight: bold;}
    textarea {
        width: 250px; min-height: 80px;
    }
</style>
