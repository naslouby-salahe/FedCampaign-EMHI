from fedcampaign_emhi.domain.types import (
    ClientBenignTally,
    ClientEligibilityRecord,
    PositiveEpochCount,
    RecordCount,
)


def build_eligibility_records(
    tallies: tuple[ClientBenignTally, ...],
    minimum_benign_event_records: RecordCount,
    minimum_nonempty_benign_epochs: PositiveEpochCount,
) -> tuple[ClientEligibilityRecord, ...]:
    records: list[ClientEligibilityRecord] = []
    for tally in sorted(tallies, key=lambda tally: tally.client_id):
        nonempty_epochs = len(tally.observed_epoch_indexes)
        eligible = (
            tally.benign_event_count >= minimum_benign_event_records
            and nonempty_epochs >= minimum_nonempty_benign_epochs
        )
        records.append(
            ClientEligibilityRecord(
                client_id=tally.client_id,
                benign_event_count=tally.benign_event_count,
                benign_nonempty_epoch_count=nonempty_epochs,
                is_eligible=eligible,
            )
        )
    return tuple(records)
