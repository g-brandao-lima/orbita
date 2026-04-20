# Phase 21: Legacy Removal - Context

**Gathered:** 2026-04-20
**Status:** Implemented (migration NAO rodada em producao)

<domain>
Remover o modelo BookingClassSnapshot (Amadeus-based signal detection do v1.0) e o amadeus_client.py legado. Booking classes nao sao mais usados: signals atuais sao baseados apenas em preco + historico.
</domain>

<decisions>
- Migration alembic f6g7h8i9j0k1_drop_booking_class_snapshots.py: DROP TABLE booking_class_snapshots
- Classe BookingClassSnapshot removida de app/models.py
- Relation FlightSnapshot.booking_classes removida
- save_flight_snapshot ignora silenciosamente campo legado "booking_classes" no dict (compat com codigo antigo que ainda passa)
- amadeus_client.py e test_amadeus_client.py deletados (Amadeus nao esta no requirements.txt)
- CI workflow atualizado para rodar pytest sem --ignore de amadeus test

**MIGRATION NAO FOI RODADA EM PRODUCAO PELA NOITE AUTONOMA.** Ao acordar:
1. Verificar que alembic upgrade head vai aplicar a migration no proximo deploy Render (buildCommand)
2. Opcional: rodar manualmente em homolog antes: `alembic upgrade head`
3. Produc~ao aplica automaticamente no proximo push para master
</decisions>

<code_context>
### Arquivos alterados
- app/models.py: removido BookingClassSnapshot e relation
- app/services/snapshot_service.py: removida logica booking_classes
- app/services/polling_service.py: removido campo booking_classes em snapshot_data
- app/routes/dashboard.py: delete_group nao mais deleta booking_class rows
- tests/test_snapshot_service.py: removido test_snapshot_has_booking_classes, ajustado test_save_flight_snapshot_function
- tests/test_amadeus_client.py: deletado
- app/services/amadeus_client.py: deletado
- alembic/versions/f6g7h8i9j0k1_drop_booking_class_snapshots.py: novo
- .github/workflows/ci.yml: pytest sem --ignore
</code_context>

<specifics>
246 testes passando apos remocao. 4 falhas pre-existentes (test_dashboard chart + test_dashboard_service price_history) por datas hardcoded.
</specifics>

<deferred>
Nenhum.
</deferred>
