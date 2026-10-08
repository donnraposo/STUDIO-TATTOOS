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
 * login quem continua autenticado.
 *
 * **Dentro de uma função, e não com `await` de nível superior.** O servidor de
 * desenvolvimento aceitava o `await` solto; o `npm run build` não — o alvo do
 * bundle cobre navegadores de 2020 em diante, e `await` de nível superior só
 * existe a partir de 2021. O defeito esperava a primeira compilação para
 * produção, que aconteceu na M8.
 *
 * Subir o alvo do build também faria compilar, e cortaria em silêncio os
 * navegadores mais antigos que alguém do estúdio possa estar usando. Uma função
 * resolve sem escolher por ninguém. */
async function start(): Promise<void> {
  await session.restore();
  createApp(App).use(router).mount("#app");
}

void start();
