class InfoBaseTaskResultBase:
    infobase_name: str = None
    succeeded: bool = None
    extras: dict = None

    def __init__(self, infobase_name, succeeded, **kwargs):
        self.infobase_name = infobase_name
        self.succeeded = succeeded
        self.extras = kwargs


class InfoBaseBackupTaskResult(InfoBaseTaskResultBase):
    backup_filename: str = None

    def __init__(self, infobase_name, succeeded, backup_filename='', **kwargs):
        super().__init__(infobase_name, succeeded, **kwargs)
        self.backup_filename = backup_filename


class InfoBaseV8TaskResult(InfoBaseTaskResultBase):

    def __init__(self, infobase_name, succeeded, **kwargs):
        super().__init__(infobase_name, succeeded, **kwargs)


class InfoBaseMaintenanceTaskResult(InfoBaseTaskResultBase):

    def __init__(self, infobase_name, succeeded, **kwargs):
        super().__init__(infobase_name, succeeded, **kwargs)


class InfoBaseAWSUploadTaskResult(InfoBaseTaskResultBase):
    upload_size: int = None

    def __init__(self, infobase_name, succeeded, upload_size=0, **kwargs):
        super().__init__(infobase_name, succeeded, **kwargs)
        self.upload_size = upload_size
