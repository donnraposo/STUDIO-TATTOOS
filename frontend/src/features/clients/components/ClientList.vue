<script setup lang="ts">
import type { Client } from "@/shared/domain/Client";
import AppButton from "@/shared/components/AppButton.vue";

/** Lista de clientes.
 *
 * Não busca nada e não sabe quem está logado: recebe a lista pronta e devolve
 * a intenção de editar. É o que a mantém utilizável na tela de agenda, quando
 * ela precisar escolher um cliente para a reserva.
 *
 * Linha, e não tabela, porque a informação por cliente é curta — nome, telefone
 * e Instagram — e a tabela obrigaria a escolher o que cortar no celular. */
defineProps<{ clients: Client[]; canEdit: boolean }>();

defineEmits<{ edit: [client: Client] }>();
</script>

<template>
  <ul class="list">
    <li
      v-for="client in clients"
      :key="client.id"
      class="row"
    >
      <div class="identity">
        <strong>{{ client.name }}</strong>
        <span class="contact">
          {{ client.phone }}
          <template v-if="client.instagram"> · {{ client.instagram }}</template>
        </span>
      </div>

      <AppButton
        v-if="canEdit"
        tone="ghost"
        @click="$emit('edit', client)"
      >
        Edit
      </AppButton>
    </li>
  </ul>
</template>

<style scoped>
.list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-0);
  padding: var(--space-0);
  list-style: none;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.identity {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.identity strong {
  font-weight: var(--weight-medium);
}

.contact {
  color: var(--color-muted);
  font-size: var(--text-label-3);
}
</style>
