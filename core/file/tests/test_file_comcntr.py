from core.file.comcntr import FileCOMControler


def test_file_control_interface_get_info_base_metadata(file_infobase, mock_file_infobases, mock_external_connection):
    """
    `get_info_base_metadata` calls `COMConnector.Connect`
    """
    fci = FileCOMControler()
    fci.get_info_base_metadata(file_infobase, "", "")
    mock_external_connection.assert_called()
