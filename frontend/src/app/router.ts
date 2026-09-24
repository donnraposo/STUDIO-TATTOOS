import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "dashboard",
    component: () => import("@/features/dashboard/DashboardView.vue"),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
