import {createApp} from 'vue'
import App from './App.vue'
import ToastService from 'primevue/toastservice';
import VueClipboard from 'vue-clipboard2';
import PrimeVue from "primevue/config";
import "primevue/resources/themes/lara-light-indigo/theme.css";

const app = createApp(App);
app.use(VueClipboard);
app.use(ToastService);
app.use(PrimeVue, {ripple: true});
app.mount('#app');
