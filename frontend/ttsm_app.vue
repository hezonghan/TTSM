<template>
    <div id="left_panel">
        <div v-for="(time_slot, depth) in time_stack" class="time_slot_button"
            :style=" 'background-color: '+(depth == global_data.displaying_depth ? 'blue' : 'green')+';' "
            @click="change_displaying_depth(depth)"
        >
            {{time_slot.short_name}}
        </div>
        
        <!-- {{time_stack[time_stack.length-1].state}}
        {{global_data.menu_task_id}} -->
        <hr/>

        <div class="button" @click="time_stack_operation('time_stack_push')" v-if="time_stack.length < time_stack_naming.length && time_stack[time_stack.length-1].state == 2">新建 {{time_stack_naming[time_stack.length]}}</div>
        
        <fieldset v-if="time_stack[time_stack.length-1].state == 1">
            <legend>新建{{time_stack[time_stack.length-1].short_name}}</legend>
            <div class="button" @click="time_stack_operation('time_slot_start')">{{time_stack[time_stack.length-1].short_name}}开始</div>
        </fieldset>

        <div class="button" @click="time_stack_operation('time_slot_stop')" v-if="time_stack.length > 1 && time_stack[time_stack.length-1].state == 2">{{time_stack[time_stack.length-1].short_name}}集合</div>

        <fieldset v-if="time_stack[time_stack.length-1].state == 3">
            <legend>{{time_stack[time_stack.length-1].short_name}}集合点评</legend>
            <!-- <input type="range" min="-1" max="3" value="0" step="1" id="time_slot_evaluation"> -->
            <span>评分:<input style="width: 90px;" type="range" min="-1" max="3" step="1" v-model.number="time_slot_evaluation"> ({{time_slot_evaluation}})</span>
            <div class="button" @click="time_stack_pop">{{time_stack[time_stack.length-1].short_name}}结束</div>
        </fieldset>

        <input style="margin-left: 20px; margin-top: 20px;" type="checkbox" v-model="global_data.show_hidden_tasks" /> 显示已隐藏任务


    </div>

    <div id="right_panel">
        <task_node :current_task_id="0" :global_data="global_data" />
    </div>
</template>

<script>
    import axios from 'axios';
    import task_node from './task_node.vue';

    export default {
        name: 'ttsm_app',
        components: {task_node},
        data() { return {
            time_stack: [],
            // popped_time_slots: [],
            time_stack_naming: [],

            time_slot_evaluation: 0,

            global_data: {  // to allow child components to modify these values.
                tasks_pool: [],
                sub_tasks: {},
                task_assigned_depth: [],

                displaying_depth: 0,
                menu_task_id: -1,
                menu_state: 0,
                show_hidden_tasks: false,
            },
        }},
        methods: {
            change_displaying_depth(depth) {
                this.global_data.displaying_depth = depth;
            },
            time_stack_operation(command_name) {
                const that = this;

                axios.post('/execute' , {
                    name: command_name,
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.time_stack = response.data.current_time_stack;
                })

            },
            time_stack_pop() {
                const that = this;

                axios.post('/execute' , {
                    name: 'time_stack_pop',
                    time_slot_evaluation: this.time_slot_evaluation,  // document.getElementById('time_slot_evaluation').value,
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.time_stack = response.data.current_time_stack;
                    if(that.global_data.displaying_depth >= that.time_stack.length) that.global_data.displaying_depth = that.time_stack.length - 1;
                })
                // console.log(this.time_slot_evaluation);
            }
        },
        created() {
            const that = this;

            axios.post('/execute' , {
                name: 'get_tasks',
            }).then(function(response) {
                that.global_data.tasks_pool = response.data.current_tasks_pool;
                that.global_data.sub_tasks = response.data.current_sub_tasks;
            });

            axios.post('/execute' , {
                name: 'get_time_stack',
            }).then(function(response) {
                that.time_stack = response.data.current_time_stack;
                that.time_stack_naming = response.data.time_stack_naming;
                // console.log(that.time_stack);
            });

            axios.post('/execute' , {
                name: 'get_assignment',
            }).then(function(response) {
                that.global_data.task_assigned_depth = response.data.current_task_assigned_depth;
            });
        },
    }
</script>

<style>
    #left_panel {
        position: fixed; left: 0px; width: 200px; top: 0; bottom: 0;
        background-color: yellow;
    }
    #right_panel {
        position: fixed; left: 200px; right: 0px; top: 0; bottom: 0;
        background-color: lime;
        overflow: scroll;
    }
    .time_slot_button {
        margin-left: 20px; margin-right: 20px; margin-top: 10px;
        border-radius: 10px;
        padding: 5px;
        color: white;
    }
    .button {
        margin-left: 20px; margin-right: 20px; margin-top: 10px;
        padding: 5px; text-align: center;
        background-color: orange;
    }
    .button:hover {font-weight: bold;}
</style>
