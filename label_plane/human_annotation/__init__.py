"""Human annotation records are independent label-plane evidence."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HumanAnnotation:
    annotator_id: str
    label: str

    def __post_init__(self) -> None:
        if not self.annotator_id or not self.label:
            raise ValueError("human annotations require annotator_id and label")


__all__ = ["HumanAnnotation"]
