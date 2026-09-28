import { createApp } from "vue";

import "@/shared/tokens.css";
import "@/shared/base.css";

import App from "@/app/App.vue";
import { router } from "@/app/router";
import { useApi } from "@/shared/api/useApi";
import { useSession } from "@/shared/session/useSession";

const { http } = useApi();
const { session } = useSession();

/** Sessão caída no meio do uso volta ao login, de qualquer tela.
 *
 * Registrado aqui, e não dentro do cliente HTTP, porque quem sabe navegar é a
 * camada de aplicação. O backend reconfere a conta a cada requisição, então
 * isto dispara de verdade quando um gestor bloqueia alguém que está usando o
 * sistema (RN 2.5). */
http.whenUnauthenticated(() => {
  session.forget();
  void router.replace({ name: "login" });
});

/** A sessão é conferida **antes** de montar.
 *
 * O cookie sobrevive ao recarregamento da página; o estado em memória, não. Sem
 * esta conferência, recarregar em qualquer rota protegida jogaria de volta ao
 * login quem continua autenticado. */
await session.restore();

createApp(App).use(router).mount("#app");
