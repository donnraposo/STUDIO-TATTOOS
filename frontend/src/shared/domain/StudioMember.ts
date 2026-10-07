import type { UserRole } from "@/shared/domain/AuthenticatedUser";

/** Alguém do estúdio, como a agenda precisa conhecer.
 *
 * `displayName` prefere o nome artístico quando existe: é como o estúdio chama
 * a pessoa no dia a dia, e é o que faz sentido num bloco da agenda. O nome
 * completo fica para telas administrativas. */
export interface StudioMember {
  id: string;
  displayName: string;
  role: UserRole;
  /** Tem agenda própria (RN 2). Proprietário e gerente entram aqui quando
   * também atuam como tatuadores — a alçada administrativa não se perde por
   * eles atenderem. */
  tattoos: boolean;
}
