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
            <span>评分:<input style="width: 90px;" type="range" min="-3" max="3" step="1" v-model.number="time_slot_evaluation"> ({{time_slot_evaluation}})</span>
            <div class="button" @click="time_stack_pop">{{time_stack[time_stack.length-1].short_name}}结束</div>
        </fieldset>

        <input style="margin-left: 20px; margin-top: 20px;" type="checkbox" v-model="global_data.show_hidden_tasks" /> 显示已隐藏任务

        <hr/>
        <div class="button" @click="open_review()">查看今日表现</div>


    </div>

    <div id="right_panel">
        <task_node :current_task_id="0" :global_data="global_data" />
    </div>

    <div id="review_window" v-if="review_opened">
        <!-- {{review_data.reviewed_unpopped_time_slots}} -->
        <!-- {{(new Date(review_data.timestamp_lo / 1000 / 1000)).toUTCString()}} -- {{(new Date(review_data.timestamp_hi / 1000 / 1000)).toUTCString()}} -->
        <!-- {{get_time_str(review_data.timestamp_lo)}} -- {{get_time_str(review_data.timestamp_hi)}} -->

        <div v-for="slot in review_data.reviewed_popped_time_slots" :style="
            'background-color: '+review_setting.color[slot.evaluation][0]+';'+
            'color: '+review_setting.color[slot.evaluation][1]+';'+
            'position: absolute;'+
            'left: '+(review_setting.width * slot.depth)+'px; width: '+(review_setting.width)+'px;'+
            'top:'+Math.max(0 , (slot.timestamp_1 - review_data.timestamp_lo) / (review_data.timestamp_hi - review_data.timestamp_lo) * 100)+'%;'+
            'height:'+((slot.timestamp_4 - Math.max(slot.timestamp_1 , review_data.timestamp_lo)) / (review_data.timestamp_hi - review_data.timestamp_lo) * 100)+'%;'+
            'border: blue 1px solid;'
        ">
            {{slot.short_name}}
            <!-- {{review_setting.bgcolor[slot.evaluation]}} -->
            <!-- <p style="font-size: 10px;">{{(new Date(slot.timestamp_1 / 1000 / 1000)).toUTCString()}}</p>
            <p style="font-size: 10px;">{{(new Date(slot.timestamp_2 / 1000 / 1000)).toUTCString()}}</p>
            <p style="font-size: 10px;">{{(new Date(slot.timestamp_3 / 1000 / 1000)).toUTCString()}}</p>
            <p style="font-size: 10px;">{{(new Date(slot.timestamp_4 / 1000 / 1000)).toUTCString()}}</p> -->

            <!-- <p style="font-size: 10px;">{{get_time_str(slot.timestamp_1)}}</p>
            <p style="font-size: 10px;">{{get_time_str(slot.timestamp_2)}}</p>
            <p style="font-size: 10px;">{{get_time_str(slot.timestamp_3)}}</p>
            <p style="font-size: 10px;">{{get_time_str(slot.timestamp_4)}}</p> -->
            <!-- {{slot.evaluation}} -->
        </div>

        <div v-for="slot in review_data.reviewed_unpopped_time_slots" :style="
            'position: absolute;'+
            'left: '+(review_setting.width * slot.depth)+'px; width: '+(review_setting.width)+'px;'+
            'top:'+Math.max(0 , (slot.timestamp_1 - review_data.timestamp_lo) / (review_data.timestamp_hi - review_data.timestamp_lo) * 100)+'%;'+
            'bottom: 0;'+
            'border: blue 1px solid;'+
            'border-bottom: dashed;'
        ">
            {{slot.short_name}}
            <!-- {{review_setting.bgcolor[slot.evaluation]}} -->
            <!-- <p style="font-size: 10px;">{{(new Date(slot.timestamp_1 / 1000 / 1000)).toUTCString()}}</p> -->
            <p style="font-size: 10px;">{{get_time_str(slot.timestamp_1)}}</p>
        </div>
        <!-- <div v-for="color in review_setting.color" style="width: 100px; height: 100px;" :style=" 'background-color: '+color[0]+'; color: '+color[1]+';' ">{{color}}</div> -->
    </div>
</template>

<script>
    import axios from 'axios';
    import task_node from './task_node.vue';

    const DAY = ['SUN' , 'MON' , 'TUE' , 'WED' , 'THU' , 'FRI' , 'SAT'];
    function add_zero(v) {return (v<=9 ? '0'+v : v);}

    export default {
        name: 'ttsm_app',
        components: {task_node},
        data() { return {
            time_stack: [],
            // popped_time_slots: [],
            time_stack_naming: [],

            time_slot_evaluation: 0,

            review_opened: false,
            review_data: {},
            review_setting: {
                color: {
                    '-3': ['purple', 'white'],
                    '-2': ['red', 'white'],
                    // '-2': ['tomato', 'white'],
                    '-1': ['orange', 'white'],// 'purple',
                    0: ['yellow', 'black'],  // 'pink',
                    1: ['greenyellow', 'black'],  // 'red',
                    2: ['lime', 'black'],  // 'orange',
                    3: ['#00c000', 'white'],  // 'yellow',
                },
                width: 200,
            },

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
            },
            open_review() {
                if(this.review_opened) {
                    this.review_opened = false;
                    return;
                }

                const that = this;

                axios.post('/execute' , {
                    name: 'review',
                    // date: '',
                }).then(function(response) {
                    if(! response.data.success) {
                        alert(response.data.reason);
                        return;
                    }
                    that.review_data = response.data.review_data;
                    that.review_opened = true;
                })
            },
            get_time_str(timestamp) {
                var d = new Date(timestamp / 1000 / 1000);
                return add_zero(d.getMonth()+1)+'-'+add_zero(d.getDate())+' '+DAY[d.getDay()]+' '+add_zero(d.getHours())+':'+add_zero(d.getMinutes());
            },
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
    #review_window {
        position: fixed; top: 50px; bottom: 50px; left: 150px; right: 150px;
        background-color: rgb(255, 255, 200); border: blue 2px solid;
    }
</style>
