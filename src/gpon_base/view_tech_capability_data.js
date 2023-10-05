import {createApp} from 'vue'
import App from './View_Tech_capability_data.vue'
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import Tooltip from 'primevue/tooltip';
import "primevue/resources/themes/lara-light-indigo/theme.css";

createApp(App)
    .use(PrimeVue)
    .use(ToastService)
    .directive('tooltip', Tooltip)
    .mount('#app')
