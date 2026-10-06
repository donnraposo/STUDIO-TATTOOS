<script setup lang="ts">
import { computed } from "vue";

import { BookingDeposit } from "@/features/payments/BookingDeposit";
import { PaymentDisplay } from "@/features/payments/PaymentDisplay";
import AppButton from "@/shared/components/AppButton.vue";
import StatusBadge from "@/shared/components/StatusBadge.vue";
import type { Payment } from "@/shared/domain/Payment";
import { MoneyFormatter } from "@/shared/format/MoneyFormatter";

/** O sinal de um agendamento, dentro da decisão sobre ele (RN-AGE-005).
 *
 * **Mora aqui porque é aqui que ele trava.** Sem recebimento confirmado o
 * horário não pode ser aprovado, e até esta etapa o gestor descobria isso pelo
 * 403 do botão de aprovar — sem nada na tela que explicasse o quê. A pergunta e
 * a resposta passam a ficar no mesmo lugar.
 *
 * **O lançamento é aqui e não na tela de pagamentos** porque um recebimento
 * pertence ou ao agendamento ou à sessão, nunca a nenhum dos dois. É aqui que a
 * origem já é conhecida; lá o gestor teria de procurar o agendamento numa lista
 * para dizer ao sistema de onde veio o dinheiro.
 *
 * Componente de apresentação: recebe por `props`, devolve por `emits`. */
const props = defineProps<{
  payments: Payment[];
  canDecide: boolean;
  busy: boolean;
}>();

defineEmits<{
  register: [];
  confirm: [payment: Payment];
  refuse: [payment: Payment];
}>();

const deposit = new BookingDeposit();
const display = new PaymentDisplay();
const money = new MoneyFormatter();

const received = computed(
  () => deposit.prepayment(props.payments) ?? deposit.live(props.payments),
);

const satisfied = computed(() => deposit.isSatisfied(props.payments));

const canRegister = computed(
  () => props.canDecide && deposit.canRegisterDeposit(props.payments),
);
</script>

<template>
  <section class="deposit">
    <header>
      <h3>Deposit</h3>
      <StatusBadge
        v-if="received"
        :label="display.status(received.status).label"
        :tone="display.status(received.status).tone"
      />
    </header>

    <p
      v-if="!received"
      class="none"
    >
      Nothing received for this booking yet. It cannot be approved until a
      payment is confirmed.
    </p>

    <template v-else>
      <p class="what">
        <strong>{{ money.amount(received.amount) }}</strong>
        <span>
          {{ display.kind(received.kind) }} · {{ display.method(received.method) }}
        </span>
      </p>

      <p
        v-if="!satisfied"
        class="blocked"
      >
        Reported, not confirmed. Check the proof of payment and confirm it —
        approval stays blocked until then.
      </p>
    </template>

    <div
      v-if="props.canDecide"
      class="actions"
    >
      <AppButton
        v-if="canRegister"
        tone="ghost"
        @click="$emit('register')"
      >
        Register payment
      </AppButton>
      <template v-if="received && received.status === 'REPORTED'">
        <AppButton
          tone="ghost"
          @click="$emit('refuse', received)"
        >
          Refuse
        </AppButton>
        <AppButton
          :busy="props.busy"
          @click="$emit('confirm', received)"
        >
          Confirm receipt
        </AppButton>
      </template>
    </div>
  </section>
</template>

<style scoped>
.deposit {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-soft);
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

h3 {
  margin: var(--space-0);
  font-size: var(--text-label-1);
}

.none,
.blocked {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.what {
  display: flex;
  flex-direction: column;
}

.what strong {
  font-weight: var(--weight-medium);
}

.what span {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}

.actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-3);
}
</style>
