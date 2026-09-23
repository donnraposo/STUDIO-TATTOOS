# Requisitos Não Funcionais

**Status:** Aprovado em alto nível; decisões técnicas parciais registradas em `04_ARQUITETURA_TECNICA.md`.  
**Última atualização:** 23/09/2026

## 1. Acesso e compatibilidade

- A primeira versão será um sistema web responsivo e instalável como PWA para computador, tablet e celular. A instalação abrirá o mesmo sistema web em uma janela própria; não será um aplicativo nativo separado.
- Acesso ao sistema estará disponível 24 horas por dia, inclusive para reservas futuras de guests.
- Notificações push no aparelho ficam para uma versão futura da PWA; e-mail e notificações dentro do sistema serão os canais iniciais.
- A interface inicial será em inglês.

## 2. Capacidade e desempenho

- Planejar capacidade para até 15 usuários simultâneos.
- Telas comuns devem responder em até 3 segundos em condições normais.
- Relatórios comuns devem responder em até 10 segundos em condições normais.
- Testes e a arquitetura deverão validar estas metas com volume realista de agenda e histórico.

## 3. Proteção e autenticação

- Conexões e dados armazenados devem receber proteção técnica básica adequada às contas, contatos, pagamentos, histórico e fotos do estúdio.
- Localização geográfica do provedor de hospedagem não é um requisito aprovado; a escolha será feita na fase de arquitetura.
- Login por e-mail e senha; não haverá autenticação em dois fatores na primeira versão.
- Encerrar sessão após 60 minutos sem atividade ou 12 horas totais.
- Bloqueio de usuário encerra suas sessões imediatamente.
- Senhas nunca serão visíveis para gestores.
- A sessão web/PWA será mantida por cookie seguro e estado validado no servidor; detalhes de biblioteca e configuração constam na arquitetura técnica.

## 4. Backup e recuperação

- Cópias de segurança automáticas e criptografadas.
- Retenção de cópias por 30 dias.
- Teste de restauração trimestral.
- A arquitetura definirá a frequência exata das cópias e os objetivos de perda máxima de dados e tempo de recuperação, sem reduzir a retenção já aprovada.

## 5. E-mail e notificações

- O serviço de e-mail será escolhido durante a arquitetura.
- O sistema deverá registrar falhas de envio e permitir tentativas de reenvio.
- Falhas de notificação não devem, por si só, alterar estado de agendamentos ou pós-vendas.
- Tentativas de agendamento bloqueadas por conflito na agenda do artista notificarão gerente e proprietário no sistema e por e-mail.
- Notificações push no aparelho, por PWA instalada e com permissão do usuário, são evolução futura.

## 6. Fora do escopo atual

- Aplicativo nativo distribuído por loja de aplicativos;
- Integração de cobrança por cartão;
- Hospedagem vinculada obrigatoriamente a uma região geográfica;
- Portal ou conta de cliente.
