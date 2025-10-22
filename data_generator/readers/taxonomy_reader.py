"""
Reader for event taxonomy from Excel/CSV files.
"""
import pandas as pd
from typing import Optional, List
from pathlib import Path

from ..models.taxonomy import (
    EventTaxonomy,
    Event,
    EventProperty,
    CommonEventProperty,
    UserProperty,
    UserIDSchema,
    PropertyType,
    UpdateMethod,
    AccountSystemType,
)


class TaxonomyReader:
    """Reads event taxonomy from Excel or CSV files"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Taxonomy file not found: {file_path}")

    def read(self) -> EventTaxonomy:
        """Read taxonomy from file"""
        if self.file_path.suffix in [".xlsx", ".xls"]:
            return self._read_excel()
        elif self.file_path.suffix == ".csv":
            return self._read_csv()
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")

    def _read_excel(self) -> EventTaxonomy:
        """Read taxonomy from Excel file"""
        # Read all sheets
        excel_file = pd.ExcelFile(self.file_path)

        taxonomy = EventTaxonomy()

        # Read User ID Schema
        if "#유저 ID 체계" in excel_file.sheet_names:
            taxonomy.user_id_schemas = self._parse_user_id_schemas(
                pd.read_excel(excel_file, sheet_name="#유저 ID 체계")
            )

        # Read Events
        if "#이벤트 데이터" in excel_file.sheet_names:
            taxonomy.events = self._parse_events(
                pd.read_excel(excel_file, sheet_name="#이벤트 데이터")
            )

        # Read Common Properties
        if "#공통 이벤트 속성" in excel_file.sheet_names:
            taxonomy.common_properties = self._parse_common_properties(
                pd.read_excel(excel_file, sheet_name="#공통 이벤트 속성")
            )

        # Read User Properties
        if "#유저 데이터" in excel_file.sheet_names:
            taxonomy.user_properties = self._parse_user_properties(
                pd.read_excel(excel_file, sheet_name="#유저 데이터")
            )

        return taxonomy

    def _read_csv(self) -> EventTaxonomy:
        """Read taxonomy from CSV file (simple format)"""
        df = pd.read_csv(self.file_path)
        # TODO: Implement CSV parsing based on format
        raise NotImplementedError("CSV format not yet implemented")

    def _parse_user_id_schemas(self, df: pd.DataFrame) -> List[UserIDSchema]:
        """Parse user ID schema sheet"""
        schemas = []

        for _, row in df.iterrows():
            # Skip rows with missing required fields
            if pd.isna(row.get("속성 이름")):
                continue

            # Parse account system type
            account_type = None
            if not pd.isna(row.get("게임 유형")):
                type_str = str(row["게임 유형"]).strip()
                # Map from Korean names
                if "단일 계정 단일" in type_str:
                    account_type = AccountSystemType.SINGLE_ACCOUNT_SINGLE_PROFILE
                elif "단일 계정 다중" in type_str:
                    account_type = AccountSystemType.SINGLE_ACCOUNT_MULTI_PROFILE
                elif "계정 시스템 없음" in type_str:
                    account_type = AccountSystemType.NO_ACCOUNT_SYSTEM

            schema = UserIDSchema(
                account_system_type=account_type,
                property_name=str(row["속성 이름"]),
                property_alias=str(row["속성 별칭"]) if not pd.isna(row.get("속성 별칭")) else None,
                property_description=str(row["속성 설명"]) if not pd.isna(row.get("속성 설명")) else None,
                value_description=str(row["값 설명"]) if not pd.isna(row.get("값 설명")) else None,
            )
            schemas.append(schema)

        return schemas

    def _parse_events(self, df: pd.DataFrame) -> List[Event]:
        """Parse events sheet"""
        events = []
        current_event: Optional[Event] = None

        for _, row in df.iterrows():
            event_name = row.get("이벤트 이름 (필수)")

            # New event row
            if not pd.isna(event_name):
                # Save previous event if exists
                if current_event:
                    events.append(current_event)

                # Create new event
                current_event = Event(
                    event_name=str(event_name),
                    event_alias=str(row["이벤트 별칭"]) if not pd.isna(row.get("이벤트 별칭")) else None,
                    event_description=str(row["이벤트 설명"]) if not pd.isna(row.get("이벤트 설명")) else None,
                    event_tag=str(row["이벤트 태그"]) if not pd.isna(row.get("이벤트 태그")) else None,
                    properties=[]
                )

            # Property row (belongs to current event)
            prop_name = row.get("속성 이름 (필수)")
            if not pd.isna(prop_name) and current_event:
                prop = EventProperty(
                    name=str(prop_name),
                    alias=str(row["속성 별칭"]) if not pd.isna(row.get("속성 별칭")) else None,
                    property_type=self._parse_property_type(row.get("속성 유형 (필수)")),
                    description=str(row["속성 설명"]) if not pd.isna(row.get("속성 설명")) else None,
                )
                current_event.properties.append(prop)

        # Don't forget the last event
        if current_event:
            events.append(current_event)

        return events

    def _parse_common_properties(self, df: pd.DataFrame) -> List[CommonEventProperty]:
        """Parse common event properties sheet"""
        properties = []

        for _, row in df.iterrows():
            # Skip rows with missing required fields
            if pd.isna(row.get("속성 이름 (필수)")):
                continue

            prop = CommonEventProperty(
                name=str(row["속성 이름 (필수)"]),
                alias=str(row["속성 별칭"]) if not pd.isna(row.get("속성 별칭")) else None,
                property_type=self._parse_property_type(row.get("속성 유형 (필수)")),
                description=str(row["속성 설명"]) if not pd.isna(row.get("속성 설명")) else None,
            )
            properties.append(prop)

        return properties

    def _parse_user_properties(self, df: pd.DataFrame) -> List[UserProperty]:
        """Parse user properties sheet"""
        properties = []

        for _, row in df.iterrows():
            # Skip rows with missing required fields
            if pd.isna(row.get("속성 이름 (필수)")):
                continue

            prop = UserProperty(
                name=str(row["속성 이름 (필수)"]),
                alias=str(row["속성 별칭"]) if not pd.isna(row.get("속성 별칭")) else None,
                property_type=self._parse_property_type(row.get("속성 유형 (필수)")),
                update_method=self._parse_update_method(row.get("업데이트 방식")),
                description=str(row["속성 설명"]) if not pd.isna(row.get("속성 설명")) else None,
                tag=str(row["속성 태그"]) if not pd.isna(row.get("속성 태그")) else None,
            )
            properties.append(prop)

        return properties

    def _parse_property_type(self, type_str: any) -> PropertyType:
        """Parse property type from string"""
        if pd.isna(type_str):
            return PropertyType.STRING

        type_str = str(type_str).lower().strip()

        if "string" in type_str or "text" in type_str:
            return PropertyType.STRING
        elif "number" in type_str or "int" in type_str or "float" in type_str:
            return PropertyType.NUMBER
        elif "bool" in type_str:
            return PropertyType.BOOLEAN
        elif "time" in type_str or "date" in type_str:
            return PropertyType.TIME
        elif "list" in type_str or "array" in type_str:
            return PropertyType.LIST
        elif "object" in type_str:
            if "group" in type_str:
                return PropertyType.OBJECT_GROUP
            return PropertyType.OBJECT
        else:
            return PropertyType.STRING

    def _parse_update_method(self, method_str: any) -> UpdateMethod:
        """Parse update method from string"""
        if pd.isna(method_str):
            return UpdateMethod.USER_SET

        method_str = str(method_str).lower().strip()

        if "set_once" in method_str:
            return UpdateMethod.USER_SET_ONCE
        elif "add" in method_str:
            return UpdateMethod.USER_ADD
        elif "append" in method_str:
            if "uniq" in method_str:
                return UpdateMethod.USER_UNIQ_APPEND
            return UpdateMethod.USER_APPEND
        elif "unset" in method_str:
            return UpdateMethod.USER_UNSET
        elif "del" in method_str:
            return UpdateMethod.USER_DEL
        else:
            return UpdateMethod.USER_SET
