import { createApp } from "vue";
import ttsm_app from './ttsm_app.vue'

document.oncontextmenu = function () { return false; };
createApp(ttsm_app).mount('#ttsm_app');
