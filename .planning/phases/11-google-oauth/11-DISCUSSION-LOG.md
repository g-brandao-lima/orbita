# Phase 11: Google OAuth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 11-google-oauth
**Areas discussed:** Fluxo de sessao, Header autenticado, Protecao de rotas, Erro e edge cases

---

## Fluxo de sessao

### Redirect apos login

| Option | Description | Selected |
|--------|-------------|----------|
| Dashboard principal | Sempre redireciona para /dashboard (index com os grupos) | ✓ |
| Pagina anterior | Volta para a pagina que o usuario tentou acessar antes do login | |
| Voce decide | Claude escolhe a melhor abordagem | |

**User's choice:** Dashboard principal
**Notes:** Simples e direto. Nao ha paginas profundas o suficiente para justificar redirect inteligente.

### Expiracao da sessao

| Option | Description | Selected |
|--------|-------------|----------|
| 7 dias | Equilibrio entre conveniencia e seguranca | |
| 30 dias | Mais conveniente, usuario raramente precisa relogar | |
| Sem expiracao | Sessao dura ate o usuario fazer logout explicitamente | ✓ |

**User's choice:** Sem expiracao
**Notes:** Uso pessoal / poucos usuarios. Conveniencia maxima.

---

## Header autenticado

| Option | Description | Selected |
|--------|-------------|----------|
| Foto + nome + dropdown | Foto circular do Google + primeiro nome, clica e abre dropdown com 'Sair' | |
| Foto + dropdown minimal | Apenas foto circular, clica e abre dropdown com nome completo + 'Sair' | |
| Voce decide | Claude escolhe o layout mais adequado ao design existente | ✓ |

**User's choice:** Voce decide
**Notes:** Claude tem discricionariedade. Deve manter coerencia com design existente (glassmorphism, Inter, dark mode).

---

## Protecao de rotas

### Comportamento para nao logado

| Option | Description | Selected |
|--------|-------------|----------|
| Redireciona para landing | Redirect silencioso para / sem mensagem | |
| Redireciona com flash | Redirect para / com flash message 'Faca login para acessar' | ✓ |
| Voce decide | Claude escolhe | |

**User's choice:** Redireciona com flash

### Estrategia de protecao

| Option | Description | Selected |
|--------|-------------|----------|
| Middleware global | Todas as rotas protegidas por padrao, exceto landing e auth | ✓ |
| Por rota (decorator) | Cada rota decide se precisa de auth | |

**User's choice:** Middleware global
**Notes:** Mais seguro. Menos chance de esquecer uma rota desprotegida.

---

## Erro e edge cases

### Falha no login

| Option | Description | Selected |
|--------|-------------|----------|
| Flash na landing | Redireciona para / com flash message descritiva | ✓ |
| Pagina de erro dedicada | Pagina /auth/error com detalhes e botao de tentar novamente | |
| Voce decide | Claude escolhe | |

**User's choice:** Flash na landing

### Conta sem foto

| Option | Description | Selected |
|--------|-------------|----------|
| Iniciais do nome | Circulo com as iniciais em cor accent | ✓ |
| Icone generico | Icone de usuario generico (silhueta) | |
| Voce decide | Claude escolhe | |

**User's choice:** Iniciais do nome
**Notes:** Mais personalizado. "GB" para Gustavo Brandao.

---

## Claude's Discretion

- Layout do avatar/nome/dropdown no header
- Modelo User (campos, tabela)
- Escolha entre SessionMiddleware ou cookie manual
- Estrutura de arquivos para auth

## Deferred Ideas

None
