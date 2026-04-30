"""Moduł Baza klientów: import z Excela, lista, edycja, pola dodatkowe."""
from __future__ import annotations

import re
from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st

from auth import ABACUS_NAVY, check_password, logout_button
from db import get_client

st.set_page_config(page_title="Baza klientów | Abacus", layout="wide")
check_password()

st.markdown(
    f"<h1 style='color:{ABACUS_NAVY};font-weight:700'>Baza klientów</h1>",
    unsafe_allow_html=True,
)

# (klucz_db, etykieta, wymagane)
CORE_FIELDS: list[tuple[str, str, bool]] = [
    ("nazwa_firmy",          "Nazwa firmy",               True),
    ("nip",                  "NIP",                       True),
    ("osoba_reprezentujaca", "Osoba reprezentująca",      False),
    ("nr_klienta",           "Nr klienta",                False),
    ("ksiegowy",             "Księgowy / Księgowa",       False),
    ("regon",                "REGON",                     False),
    ("krs",                  "KRS",                       False),
    ("pesel",                "PESEL",                     False),
    ("ulica",                "Ulica",                     False),
    ("kod_pocztowy",         "Kod pocztowy",              False),
    ("miasto",               "Miasto",                    False),
    ("email",                "Mail",                      False),
    ("telefon",              "Telefon",                   False),
    ("forma_dzialalnosci",   "Forma działalności",        False),
    ("data_zawarcia_umowy",  "Data zawarcia umowy",       False),
    ("platnik_vat",          "Płatnik VAT",               False),
    ("ma_pracownikow",       "Zatrudnia pracowników",     False),
    ("rodzaj_ksiegowosci",   "Rodzaj księgowości",        False),
    ("rodzaj_umowy",         "Rodzaj umowy",              False),
]

BOOL_FIELDS = {"platnik_vat", "ma_pracownikow"}
KSIEGOWOSC_VALUES = {"KH", "KPiR", "Ryczalt"}
UMOWA_VALUES = {"UoP", "UZ", "UoD"}

TRUE_TOKENS  = {"true", "tak", "t", "1", "yes", "y", "prawda"}
FALSE_TOKENS = {"false", "nie", "n", "0", "no", "f", "falsz", "fałsz"}

DISPLAY_COLS = [
    "nr_klienta", "nazwa_firmy", "nip", "email", "telefon",
    "forma_dzialalnosci", "rodzaj_ksiegowosci", "platnik_vat",
    "ma_pracownikow", "ksiegowy", "aktywny",
]


def to_bool(value: Any) -> bool | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))
    text = str(value).strip().lower()
    if not text:
        return None
    if text in TRUE_TOKENS:
        return True
    if text in FALSE_TOKENS:
        return False
    return None


def clean_str(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def normalize_nip(value: Any) -> str | None:
    text = clean_str(value)
    if text is None:
        return None
    return re.sub(r"[\s\-]", "", text)


def normalize_date(value: Any) -> str | None:
    """Normalizuje datę do YYYY-MM-DD. Obsługuje: 26.07.2023, 26.07.2023 r., 2023-07-26."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = re.sub(r"\s*r\.?\s*$", "", str(value).strip()).strip()
    if not text:
        return None
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", text)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        return text
    try:
        return pd.to_datetime(text, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def show_supabase_error(prefix: str, exc: Exception) -> None:
    st.error(f"{prefix}: {exc}")


@st.cache_data(ttl=30, show_spinner=False)
def fetch_clients() -> pd.DataFrame:
    client = get_client()
    res = client.table("clients").select("*").order("nazwa_firmy").execute()
    return pd.DataFrame(res.data or [])


@st.cache_data(ttl=30, show_spinner=False)
def fetch_extra_fields() -> pd.DataFrame:
    client = get_client()
    res = client.table("extra_fields").select("*").order("id").execute()
    return pd.DataFrame(res.data or [])


def refresh_caches() -> None:
    fetch_clients.clear()
    fetch_extra_fields.clear()


tab_import, tab_list, tab_extra = st.tabs(
    ["Import z Excela", "Lista klientów", "Pola dodatkowe"]
)


# ============================================================================
# TAB 1: Import z Excela
# ============================================================================
with tab_import:
    st.subheader("Import klientów z pliku Excel/CSV")

    uploaded = st.file_uploader(
        "Wybierz plik (.xlsx, .xls lub .csv)",
        type=["xlsx", "xls", "csv"],
        key="import_file",
    )

    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith(".csv"):
                df_in = pd.read_csv(uploaded)
            else:
                df_in = pd.read_excel(uploaded)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Nie udało się odczytać pliku: {exc}")
            df_in = None

        if df_in is not None and not df_in.empty:
            st.markdown("**Podgląd (pierwsze 5 wierszy)**")
            st.dataframe(df_in.head(5), use_container_width=True)

            st.markdown("**Mapowanie kolumn**")
            file_columns = ["— pomiń —"] + list(df_in.columns.astype(str))
            mapping: dict[str, str] = {}
            cols_a, cols_b = st.columns(2)
            for idx, (key, label, required) in enumerate(CORE_FIELDS):
                target = cols_a if idx % 2 == 0 else cols_b
                default_idx = 0
                for i, col in enumerate(file_columns):
                    if col.strip().lower().replace(" ", "_") == key:
                        default_idx = i
                        break
                with target:
                    suffix = " *" if required else ""
                    mapping[key] = st.selectbox(
                        f"{label}{suffix}",
                        file_columns,
                        index=default_idx,
                        key=f"map_{key}",
                    )

            mode = st.radio(
                "Tryb importu",
                ["Dodaj nowe / Nadpisz istniejące (po NIP)", "Tylko dodaj nowe (pomiń istniejące)"],
                key="import_mode",
            )

            if st.button("Importuj", type="primary"):
                missing_required = [
                    label for key, label, req in CORE_FIELDS
                    if req and mapping.get(key) == "— pomiń —"
                ]
                if missing_required:
                    st.error("Brakuje wymaganych mapowań: " + ", ".join(missing_required))
                    st.stop()

                records: list[dict] = []
                row_errors: list[str] = []
                seen_nips: set[str] = set()
                duplicate_nips: set[str] = set()

                for row_idx, row in df_in.iterrows():
                    record: dict[str, Any] = {}
                    for key, _, _ in CORE_FIELDS:
                        src_col = mapping.get(key)
                        if not src_col or src_col == "— pomiń —":
                            continue
                        raw = row.get(src_col)
                        if key == "nip":
                            record[key] = normalize_nip(raw)
                        elif key == "data_zawarcia_umowy":
                            v = normalize_date(raw)
                            if v is not None:
                                record[key] = v
                        elif key in BOOL_FIELDS:
                            b = to_bool(raw)
                            if b is not None:
                                record[key] = b
                        elif key == "rodzaj_ksiegowosci":
                            v = clean_str(raw)
                            if v and v not in KSIEGOWOSC_VALUES:
                                row_errors.append(
                                    f"Wiersz {row_idx + 2}: nieprawidłowy rodzaj_ksiegowosci '{v}'"
                                )
                                v = None
                            if v:
                                record[key] = v
                        elif key == "rodzaj_umowy":
                            v = clean_str(raw)
                            if v and v not in UMOWA_VALUES:
                                row_errors.append(
                                    f"Wiersz {row_idx + 2}: nieprawidłowy rodzaj_umowy '{v}'"
                                )
                                v = None
                            if v:
                                record[key] = v
                        else:
                            v = clean_str(raw)
                            if v is not None:
                                record[key] = v

                    if not record.get("nazwa_firmy"):
                        row_errors.append(f"Wiersz {row_idx + 2}: brak nazwa_firmy")
                        continue
                    if not record.get("nip"):
                        row_errors.append(f"Wiersz {row_idx + 2}: brak NIP")
                        continue

                    nip = record["nip"]
                    if nip in seen_nips:
                        duplicate_nips.add(nip)
                        continue
                    seen_nips.add(nip)
                    records.append(record)

                if duplicate_nips:
                    st.warning(f"Pominięto duplikaty NIP w pliku: {', '.join(sorted(duplicate_nips))}")

                if not records:
                    st.error("Brak prawidłowych rekordów do importu.")
                    if row_errors:
                        with st.expander(f"Błędy walidacji ({len(row_errors)})"):
                            for e in row_errors:
                                st.write("• " + e)
                    st.stop()

                client = get_client()
                added = updated = errors = 0
                error_messages: list[str] = []

                try:
                    existing_resp = (
                        client.table("clients")
                        .select("nip")
                        .in_("nip", [r["nip"] for r in records])
                        .execute()
                    )
                    existing_nips = {row["nip"] for row in (existing_resp.data or [])}
                except Exception as exc:  # noqa: BLE001
                    show_supabase_error("Błąd przy sprawdzaniu duplikatów", exc)
                    st.stop()

                progress = st.progress(0.0, text="Importowanie...")
                total = len(records)

                if mode.startswith("Dodaj nowe / Nadpisz"):
                    BATCH = 100
                    for i in range(0, total, BATCH):
                        batch = records[i: i + BATCH]
                        try:
                            client.table("clients").upsert(batch, on_conflict="nip").execute()
                            for r in batch:
                                if r["nip"] in existing_nips:
                                    updated += 1
                                else:
                                    added += 1
                        except Exception as exc:  # noqa: BLE001
                            errors += len(batch)
                            error_messages.append(str(exc))
                        progress.progress(min((i + BATCH) / total, 1.0))
                else:
                    new_records = [r for r in records if r["nip"] not in existing_nips]
                    BATCH = 100
                    for i in range(0, len(new_records), BATCH):
                        batch = new_records[i: i + BATCH]
                        try:
                            client.table("clients").insert(batch).execute()
                            added += len(batch)
                        except Exception as exc:  # noqa: BLE001
                            errors += len(batch)
                            error_messages.append(str(exc))
                        progress.progress(min((i + BATCH) / max(len(new_records), 1), 1.0))
                    progress.progress(1.0)

                progress.empty()
                st.success(f"Import zakończony. Dodano: {added}, zaktualizowano: {updated}, błędy: {errors + len(row_errors)}.")
                if row_errors:
                    with st.expander(f"Błędy walidacji wierszy ({len(row_errors)})"):
                        for e in row_errors:
                            st.write("• " + e)
                if error_messages:
                    with st.expander(f"Błędy zapisu ({len(error_messages)})"):
                        for e in error_messages:
                            st.write("• " + e)
                refresh_caches()


# ============================================================================
# TAB 2: Lista klientów
# ============================================================================
with tab_list:
    st.subheader("Lista klientów")

    try:
        df = fetch_clients()
    except Exception as exc:  # noqa: BLE001
        show_supabase_error("Nie udało się pobrać klientów", exc)
        df = pd.DataFrame()

    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        search = st.text_input("Szukaj po nazwie / NIP", key="filter_search")
    with f2:
        f_ksieg = st.selectbox(
            "Rodzaj księgowości",
            ["Wszystkie", "KH", "KPiR", "Ryczalt"],
            key="filter_ksieg",
        )
    with f3:
        f_vat = st.selectbox("Płatnik VAT", ["Wszyscy", "Tak", "Nie"], key="filter_vat")
    with f4:
        f_aktywny = st.selectbox("Status", ["Aktywni", "Wszyscy", "Nieaktywni"], key="filter_aktywny")

    filtered = df.copy()
    if not filtered.empty:
        if search:
            s = search.strip().lower()
            mask = (
                filtered["nazwa_firmy"].fillna("").str.lower().str.contains(s)
                | filtered["nip"].fillna("").str.lower().str.contains(s)
            )
            filtered = filtered[mask]
        if f_ksieg != "Wszystkie":
            filtered = filtered[filtered["rodzaj_ksiegowosci"] == f_ksieg]
        if f_vat != "Wszyscy":
            filtered = filtered[filtered["platnik_vat"] == (f_vat == "Tak")]
        if f_aktywny == "Aktywni":
            filtered = filtered[filtered["aktywny"] == True]   # noqa: E712
        elif f_aktywny == "Nieaktywni":
            filtered = filtered[filtered["aktywny"] == False]  # noqa: E712

    visible_cols = [c for c in DISPLAY_COLS if c in filtered.columns]
    st.dataframe(
        filtered[visible_cols] if visible_cols else filtered,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Liczba klientów: {len(filtered)}")

    if not filtered.empty:
        export_buf = BytesIO()
        with pd.ExcelWriter(export_buf, engine="openpyxl") as writer:
            filtered.to_excel(writer, index=False, sheet_name="Klienci")
        st.download_button(
            "Eksportuj do Excel",
            data=export_buf.getvalue(),
            file_name="klienci.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")
    st.subheader("Edycja klienta")

    if df.empty:
        st.info("Brak klientów do edycji.")
    else:
        options = {
            int(row["id"]): f"{row['nazwa_firmy']} ({row['nip']})"
            for _, row in df.iterrows()
        }
        selected_id = st.selectbox(
            "Wybierz klienta",
            options=list(options.keys()),
            format_func=lambda i: options[i],
            key="edit_client_select",
        )
        client_row = df[df["id"] == selected_id].iloc[0].to_dict()

        with st.form("edit_client_form"):
            c1, c2 = st.columns(2)
            with c1:
                e_nazwa  = st.text_input("Nazwa firmy *",        value=client_row.get("nazwa_firmy") or "")
                e_nip    = st.text_input("NIP *",                value=client_row.get("nip") or "")
                e_osoba  = st.text_input("Osoba reprezentująca", value=client_row.get("osoba_reprezentujaca") or "")
                e_nr     = st.text_input("Nr klienta",           value=client_row.get("nr_klienta") or "")
                e_ks     = st.text_input("Księgowy / Księgowa",  value=client_row.get("ksiegowy") or "")
                e_regon  = st.text_input("REGON",                value=client_row.get("regon") or "")
                e_krs    = st.text_input("KRS",                  value=client_row.get("krs") or "")
                e_pesel  = st.text_input("PESEL",                value=client_row.get("pesel") or "")
                e_ulica  = st.text_input("Ulica",                value=client_row.get("ulica") or "")
                e_kod    = st.text_input("Kod pocztowy",         value=client_row.get("kod_pocztowy") or "")
                e_miasto = st.text_input("Miasto",               value=client_row.get("miasto") or "")
            with c2:
                e_email   = st.text_input("Mail",                value=client_row.get("email") or "")
                e_telefon = st.text_input("Telefon",             value=client_row.get("telefon") or "")
                e_forma   = st.text_input("Forma działalności",  value=client_row.get("forma_dzialalnosci") or "")
                e_data    = st.text_input("Data zawarcia umowy", value=str(client_row.get("data_zawarcia_umowy") or ""))
                ksieg_opts = ["", "KH", "KPiR", "Ryczalt"]
                e_rk = st.selectbox(
                    "Rodzaj księgowości",
                    ksieg_opts,
                    index=ksieg_opts.index(client_row.get("rodzaj_ksiegowosci") or ""),
                )
                umowa_opts = ["", "UoP", "UZ", "UoD"]
                e_ru = st.selectbox(
                    "Rodzaj umowy",
                    umowa_opts,
                    index=umowa_opts.index(client_row.get("rodzaj_umowy") or ""),
                )
                e_vat     = st.checkbox("Płatnik VAT",           value=bool(client_row.get("platnik_vat")))
                e_prac    = st.checkbox("Zatrudnia pracowników", value=bool(client_row.get("ma_pracownikow")))
                e_aktywny = st.checkbox("Aktywny",               value=bool(client_row.get("aktywny")))

            sb1, sb2 = st.columns(2)
            with sb1:
                save = st.form_submit_button("Zapisz zmiany", type="primary")
            with sb2:
                deactivate = st.form_submit_button("Dezaktywuj")

        if save:
            if not e_nazwa.strip() or not e_nip.strip():
                st.error("Nazwa firmy i NIP są wymagane.")
            else:
                update = {
                    "nazwa_firmy":          e_nazwa.strip(),
                    "nip":                  normalize_nip(e_nip),
                    "osoba_reprezentujaca": e_osoba.strip() or None,
                    "nr_klienta":           e_nr.strip() or None,
                    "ksiegowy":             e_ks.strip() or None,
                    "regon":                e_regon.strip() or None,
                    "krs":                  e_krs.strip() or None,
                    "pesel":                e_pesel.strip() or None,
                    "ulica":                e_ulica.strip() or None,
                    "kod_pocztowy":         e_kod.strip() or None,
                    "miasto":               e_miasto.strip() or None,
                    "email":                e_email.strip() or None,
                    "telefon":              e_telefon.strip() or None,
                    "forma_dzialalnosci":   e_forma.strip() or None,
                    "data_zawarcia_umowy":  e_data.strip() or None,
                    "rodzaj_ksiegowosci":   e_rk or None,
                    "rodzaj_umowy":         e_ru or None,
                    "platnik_vat":          e_vat,
                    "ma_pracownikow":       e_prac,
                    "aktywny":              e_aktywny,
                }
                try:
                    get_client().table("clients").update(update).eq("id", int(selected_id)).execute()
                    st.success("Zapisano zmiany.")
                    refresh_caches()
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    show_supabase_error("Błąd zapisu", exc)

        if deactivate:
            try:
                get_client().table("clients").update({"aktywny": False}).eq("id", int(selected_id)).execute()
                st.success("Klient dezaktywowany.")
                refresh_caches()
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                show_supabase_error("Błąd dezaktywacji", exc)


# ============================================================================
# TAB 3: Pola dodatkowe
# ============================================================================
with tab_extra:
    st.subheader("Pola dodatkowe")

    try:
        ef = fetch_extra_fields()
    except Exception as exc:  # noqa: BLE001
        show_supabase_error("Nie udało się pobrać pól dodatkowych", exc)
        ef = pd.DataFrame()

    if ef.empty:
        st.info("Nie zdefiniowano jeszcze żadnych pól dodatkowych.")
    else:
        for _, row in ef.iterrows():
            c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
            c1.write(f"**{row['field_key']}**")
            c2.write(row["field_label"])
            c3.write(row["field_type"])
            if c4.button("Usuń", key=f"del_{row['field_key']}"):
                try:
                    get_client().table("extra_fields").delete().eq("field_key", row["field_key"]).execute()
                    st.success(f"Usunięto pole: {row['field_key']}")
                    refresh_caches()
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    show_supabase_error("Błąd usuwania", exc)

    st.markdown("---")
    st.markdown("**Dodaj nowe pole**")

    with st.form("add_extra_field"):
        n1, n2, n3 = st.columns(3)
        with n1:
            new_key = st.text_input("Klucz pola (litery, cyfry, _)")
        with n2:
            new_label = st.text_input("Etykieta (czytelna nazwa)")
        with n3:
            new_type = st.selectbox("Typ", ["text", "number", "boolean"])
        add_btn = st.form_submit_button("Dodaj pole", type="primary")

    if add_btn:
        key = (new_key or "").strip()
        label = (new_label or "").strip()
        if not key or not label:
            st.error("Klucz i etykieta są wymagane.")
        elif not re.fullmatch(r"[A-Za-z0-9_]+", key):
            st.error("Klucz może zawierać tylko litery, cyfry i podkreślnik.")
        else:
            try:
                get_client().table("extra_fields").insert(
                    {"field_key": key, "field_label": label, "field_type": new_type}
                ).execute()
                st.success(f"Dodano pole: {key}")
                refresh_caches()
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                show_supabase_error("Błąd dodawania pola", exc)


logout_button()
