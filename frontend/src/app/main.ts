import { createApp } from "vue";

import "@/shared/tokens.css";
import "@/shared/base.css";

import App from "@/app/App.vue";
import { router } from "@/app/router";

createApp(App).use(router).mount("#app");
