import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AppShell from "@/app/AppShell.vue";
import { useSession } from "@/shared/session/useSession";

/** Rotas da aplicação.
 *
 * As protegidas ficam **dentro** da casca, como filhas: a casca só existe para
 * quem entrou, e aninhar evita que cada tela precise lembrar de desenhá-la.
 *
 * A entrada definida para o MVP é a agenda do dia. Enquanto a visão geral não
 * for substituída por ela, `home` responde por `/`.
 *
 * **Não há rota escondida por perfil.** `/quotes` existe para todo mundo, e o
 * guest que digitar o endereço recebe 403 do backend (RN-ORC-001). Esconder o
 * item de menu é cortesia; a tranca é do servidor. */
const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/features/auth/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: AppShell,
    children: [
      {
        path: "",
        name: "home",
        component: () => import("@/features/home/HomeView.vue"),
      },
      {
        path: "schedule",
        name: "schedule",
        component: () => import("@/features/scheduling/SchedulingView.vue"),
      },
      {
        path: "clients",
        name: "clients",
        component: () => import("@/features/clients/ClientsView.vue"),
      },
      {
        path: "quotes",
        name: "quotes",
        component: () => import("@/features/quotes/QuotesView.vue"),
      },
      {
        path: "status",
        name: "status",
        component: () => import("@/features/dashboard/DashboardView.vue"),
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

/** Guarda de acesso.
 *
 * A sessão já foi conferida com o servidor antes de a aplicação montar, então
 * aqui basta ler o estado. Fazer a conferência dentro da guarda faria cada
 * navegação pagar uma requisição, e pior, a primeira delas veria o usuário
 * ainda nulo e mandaria ao login quem estava autenticado.
 *
 * Quem já entrou e tenta abrir `/login` vai para a aplicação: mostrar o
 * formulário a quem tem sessão é convite a sair sem querer. */
router.beforeEach((to) => {
  const { session } = useSession();
  const authenticated = session.user.value !== null;

  if (to.meta.public) {
    return authenticated ? { name: "home" } : true;
  }

  return authenticated ? true : { name: "login", query: { redirect: to.fullPath } };
});
