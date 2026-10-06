<script setup lang="ts">
import { AccountDisplay } from "@/features/accounts/AccountDisplay";
import { AccountManagementReach } from "@/features/accounts/AccountManagementReach";
import AppButton from "@/shared/components/AppButton.vue";
import AppCard from "@/shared/components/AppCard.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { AuthenticatedUser } from "@/shared/domain/AuthenticatedUser";
import type { StudioAccount } from "@/shared/domain/StudioAccount";

/** As contas do estúdio, com o que cada uma permite fazer (RN 2.1 a 2.6).
 *
 * **Mostra as bloqueadas.** Esconder a conta sem acesso esconderia o botão que
 * devolve o acesso a ela.
 *
 * Os botões aparecem conforme a alçada de quem olha, e isso é cortesia: o
 * gerente não vê "Block" num proprietário porque o servidor o recusaria de
 * todo modo. Quem decide é o backend.
 *
 * Recebe o ator por `props` em vez de ler a sessão — é componente de
 * apresentação, e ler a sessão aqui o amarraria à aplicação inteira.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  accounts: StudioAccount[];
  actor: AuthenticatedUser;
  busy: boolean;
}>();

defineEmits<{
  setShare: [account: StudioAccount];
  block: [account: StudioAccount];
  unblock: [account: StudioAccount];
}>();

const display = new AccountDisplay();
const reach = new AccountManagementReach();
</script>

<template>
  <ul class="list">
    <li
      v-for="account in props.accounts"
      :key="account.id"
    >
      <AppCard>
        <template #header>
          <div class="who">
            <strong>{{ display.name(account) }}</strong>
            <small>{{ display.role(account.role) }}</small>
          </div>
          <StatusBadge
            :label="display.status(account.status).label"
            :tone="display.status(account.status).tone"
          />
        </template>

        <dl class="facts">
          <div>
            <dt>Email</dt>
            <dd>{{ account.email }}</dd>
          </div>
          <div>
            <dt>Phone</dt>
            <dd>{{ account.phone }}</dd>
          </div>
          <div v-if="display.canSetShare(account)">
            <dt>Share</dt>
            <dd class="share">
              {{ display.share(account) }}
            </dd>
          </div>
        </dl>

        <template #footer>
          <AppButton
            v-if="reach.canSetShare(props.actor, account)"
            tone="ghost"
            @click="$emit('setShare', account)"
          >
            Share
          </AppButton>
          <AppButton
            v-if="reach.canChangeStatus(props.actor, account) && account.status === 'BLOCKED'"
            :busy="props.busy"
            @click="$emit('unblock', account)"
          >
            Restore access
          </AppButton>
          <AppButton
            v-else-if="reach.canChangeStatus(props.actor, account)"
            tone="danger"
            :busy="props.busy"
            @click="$emit('block', account)"
          >
            Block
          </AppButton>
        </template>
      </AppCard>
    </li>
  </ul>
</template>

<style scoped>
.list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--track-card-min), 1fr));
  gap: var(--space-4);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.who {
  display: flex;
  flex-direction: column;
}

.who strong {
  font-weight: var(--weight-medium);
}

.who small {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.facts {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
}

dt {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

dd {
  margin: var(--space-0);
  overflow-wrap: anywhere;
}

/* O percentual é o número que o acordo define, e o gestor o procura ao
   percorrer a lista. */
.share {
  font-weight: var(--weight-medium);
}
</style>
