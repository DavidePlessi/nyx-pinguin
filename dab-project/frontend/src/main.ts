import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await originalFetch(...args);
    if (response.status === 401) {
        localStorage.removeItem('dab_session_token');
        if (router.currentRoute.value.name !== 'Login') {
            router.push({ name: 'Login' });
        }
    }
    return response;
};

const app = createApp(App)

app.use(router)

app.mount('#app')
