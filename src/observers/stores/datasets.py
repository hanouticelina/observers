import atexit
import json
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional

from huggingface_hub import CommitScheduler, login, whoami

from observers.stores.base import Store

DEFAULT_DATA_FOLDER = "store"


@dataclass
class DatasetsStore(Store):
    """
    Datasets store
    """

    org_name: Optional[str] = field(default=None)
    repo_name: Optional[str] = field(default=None)
    folder_path: Optional[str] = field(default=DEFAULT_DATA_FOLDER)
    every: Optional[int] = field(default=5)
    path_in_repo: Optional[str] = field(default=None)
    revision: Optional[str] = field(default=None)
    private: Optional[bool] = field(default=None)
    token: Optional[str] = field(default=None)
    allow_patterns: Optional[List[str]] = field(default=None)
    ignore_patterns: Optional[List[str]] = field(default=None)
    squash_history: Optional[bool] = field(default=None)

    _scheduler: Optional[CommitScheduler] = None

    def __post_init__(self):
        """Initialize the store"""
        try:
            whoami(token=self.token or os.getenv("HF_TOKEN"))
        except Exception:
            login()

    def _init_table(self, record: "Record"):
        repo_name = self.repo_name or record.table_name
        org_name = self.org_name or whoami(token=self.token)["name"]
        repo_id = f"{org_name}/{repo_name}"
        self._scheduler = CommitScheduler(
            repo_id=repo_id,
            folder_path=self.folder_path or DEFAULT_DATA_FOLDER,
            every=self.every,
            path_in_repo=self.path_in_repo,
            repo_type="dataset",
            revision=self.revision,
            private=self.private,
            token=self.token,
            allow_patterns=self.allow_patterns,
            ignore_patterns=self.ignore_patterns,
            squash_history=self.squash_history,
        )
        atexit.register(self._scheduler.push_to_hub)

    @classmethod
    def connect(
        cls,
        org_name: Optional[str] = None,
        repo_name: Optional[str] = None,
        folder_path: Optional[str] = DEFAULT_DATA_FOLDER,
        every: Optional[int] = 5,
        path_in_repo: Optional[str] = None,
        revision: Optional[str] = None,
        private: Optional[bool] = None,
        token: Optional[str] = None,
        allow_patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        squash_history: Optional[bool] = None,
    ) -> "DatasetsStore":
        """Create a new store instance with optional custom path"""
        return cls(
            org_name=org_name,
            repo_name=repo_name,
            folder_path=folder_path,
            every=every,
            path_in_repo=path_in_repo,
            revision=revision,
            private=private,
            token=token,
            allow_patterns=allow_patterns,
            ignore_patterns=ignore_patterns,
            squash_history=squash_history,
        )

    def add(self, record: "Record"):
        """Add a new record to the database"""
        if not self._scheduler:
            self._init_table(record)

        with self._scheduler.lock:
            with (self._scheduler.folder_path / f"data_{record.table_name}.json").open(
                "a"
            ) as f:
                record_dict = asdict(record)
                record_dict["synced_at"] = None

                for json_field in record.json_fields:
                    if record_dict[json_field]:
                        record_dict[json_field] = json.dumps(record_dict[json_field])

                f.write(json.dumps(record_dict))