/** Um item colocado numa faixa horizontal, com a trilha em que ele coube. */
export interface Packed<T> {
  item: T;
  track: number;
}

/** Distribui itens sobrepostos em trilhas dentro da mesma maca.
 *
 * **É o que a RN-AGE-004 exige.** Uma solicitação pendente não bloqueia a maca,
 * então dois artistas podem pedir o mesmo horário e as duas solicitações
 * precisam ser **exibidas juntas**. Empilhadas na mesma linha, a de cima
 * esconderia a de baixo — e o gestor decidiria sem saber que havia concorrência.
 *
 * O algoritmo é o guloso de partição de intervalos: percorre em ordem de
 * início e põe cada item na primeira trilha já livre naquele ponto, criando
 * outra só quando nenhuma serve. Isso usa o menor número de trilhas possível,
 * o que importa porque cada trilha extra aumenta a altura da linha da maca.
 *
 * Classe pura, sem Vue: é geometria, e se testa sem montar tela. */
export class LanePacker {
  pack<T>(items: T[], extent: (item: T) => { column: number; span: number }): Packed<T>[] {
    const ordered = [...items].sort((left, right) => extent(left).column - extent(right).column);
    const trackEnds: number[] = [];
    const packed: Packed<T>[] = [];

    for (const item of ordered) {
      const { column, span } = extent(item);
      const track = trackEnds.findIndex((end) => end <= column);
      const chosen = track === -1 ? trackEnds.length : track;
      trackEnds[chosen] = column + span;
      packed.push({ item, track: chosen });
    }

    return packed;
  }

  /** Quantas trilhas o conjunto ocupa. A linha da maca cresce por isto. */
  trackCount<T>(packed: Packed<T>[]): number {
    return packed.reduce((highest, entry) => Math.max(highest, entry.track + 1), 1);
  }
}
