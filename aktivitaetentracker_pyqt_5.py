import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QHeaderView, QComboBox
)
from PyQt5.QtCore import Qt


class AktivitaetenTracker(QWidget):
    DATEINAME = "Aktivitätenliste.txt"

    SPALTEN = [
        "Datum",
        "Ort",
        "Startzeit",
        "Mittagspause Anfang",
        "Mittagspause Ende",
        "Ende",
        "Gesamtzeit",
        "Tätigkeiten",
    ]

    ORT_OPTIONEN = ["Vor Ort", "HO"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aktivitätentracker")
        self.resize(1300, 600)

        self._lade_aktiv = False

        self.init_ui()
        self.lade_datei()

    def init_ui(self):
        hauptlayout = QVBoxLayout()

        eingabe_layout = QHBoxLayout()
        label = QLabel("Tätigkeitskommentar:")
        self.taetigkeit_input = QLineEdit()
        self.taetigkeit_input.setPlaceholderText("Kommentar zur aktuellen Tätigkeit eingeben...")

        self.button = QPushButton("Zeitstempel eintragen")
        self.button.clicked.connect(self.zeitstempel_eintragen)

        eingabe_layout.addWidget(label)
        eingabe_layout.addWidget(self.taetigkeit_input)
        eingabe_layout.addWidget(self.button)

        summen_layout = QHBoxLayout()
        self.ho_label = QLabel("Gesamt HO: 00:00")
        self.vorort_label = QLabel("Gesamt Vor Ort: 00:00")
        self.gesamt_label = QLabel("Gesamt Alles: 00:00")

        summen_layout.addWidget(self.ho_label)
        summen_layout.addSpacing(30)
        summen_layout.addWidget(self.vorort_label)
        summen_layout.addSpacing(30)
        summen_layout.addWidget(self.gesamt_label)
        summen_layout.addStretch()

        self.tabelle = QTableWidget()
        self.tabelle.setColumnCount(len(self.SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(self.SPALTEN)
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.itemChanged.connect(self.tabelle_geaendert)

        header = self.tabelle.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        self.tabelle.setColumnWidth(0, 95)
        self.tabelle.setColumnWidth(1, 90)
        self.tabelle.setColumnWidth(2, 80)
        self.tabelle.setColumnWidth(3, 140)
        self.tabelle.setColumnWidth(4, 140)
        self.tabelle.setColumnWidth(5, 80)
        self.tabelle.setColumnWidth(6, 90)

        hauptlayout.addLayout(eingabe_layout)
        hauptlayout.addLayout(summen_layout)
        hauptlayout.addWidget(self.tabelle)
        self.setLayout(hauptlayout)

    def closeEvent(self, event):
        self.speichere_datei()
        event.accept()

    def heutiges_datum(self):
        return datetime.now().strftime("%d.%m.%Y")

    def aktuelle_zeit(self):
        return datetime.now().strftime("%H:%M")

    def finde_zeile_fuer_heute(self):
        datum_heute = self.heutiges_datum()
        for zeile in range(self.tabelle.rowCount()):
            item = self.tabelle.item(zeile, 0)
            if item and item.text() == datum_heute:
                return zeile
        return -1

    def erstelle_ort_combobox(self, wert="Vor Ort"):
        combo = QComboBox()
        combo.addItems(self.ORT_OPTIONEN)
        index = combo.findText(wert)
        if index >= 0:
            combo.setCurrentIndex(index)
        combo.currentIndexChanged.connect(self.ort_geaendert)
        return combo

    def neue_zeile_anlegen(self, datum):
        zeile = self.tabelle.rowCount()
        self.tabelle.insertRow(zeile)

        for spalte in range(len(self.SPALTEN)):
            if spalte == 1:
                continue

            item = QTableWidgetItem("")

            if spalte == 0:
                item.setText(datum)

            if spalte == 6:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            self.tabelle.setItem(zeile, spalte, item)

        combo = self.erstelle_ort_combobox("Vor Ort")
        self.tabelle.setCellWidget(zeile, 1, combo)

        return zeile

    def naechste_freie_zeitspalte(self, zeile):
        for spalte in [2, 3, 4, 5]:
            item = self.tabelle.item(zeile, spalte)
            if not item or not item.text().strip():
                return spalte
        return -1

    def zeitstempel_eintragen(self):
        kommentar = self.taetigkeit_input.text().strip()
        datum_heute = self.heutiges_datum()
        zeit = self.aktuelle_zeit()

        zeile = self.finde_zeile_fuer_heute()
        if zeile == -1:
            zeile = self.neue_zeile_anlegen(datum_heute)

        spalte = self.naechste_freie_zeitspalte(zeile)
        if spalte == -1:
            QMessageBox.information(
                self,
                "Hinweis",
                "Alle Zeitfelder für den heutigen Tag sind bereits ausgefüllt."
            )
            return

        self._lade_aktiv = True
        self.tabelle.item(zeile, spalte).setText(zeit)

        if kommentar:
            item = self.tabelle.item(zeile, 7)
            if item and item.text().strip():
                item.setText(item.text() + " | " + kommentar)
            else:
                self.tabelle.setItem(zeile, 7, QTableWidgetItem(kommentar))

        self._lade_aktiv = False

        self.berechne_gesamtzeit_fuer_zeile(zeile)
        self.aktualisiere_summenanzeige()
        self.speichere_datei()
        self.taetigkeit_input.clear()

    def ort_geaendert(self):
        if self._lade_aktiv:
            return
        self.aktualisiere_summenanzeige()
        self.speichere_datei()

    def tabelle_geaendert(self, item):
        if self._lade_aktiv:
            return

        spalte = item.column()

        if spalte in [2, 3, 4, 5]:
            self._lade_aktiv = True
            self.normalisiere_zeitfeld(item)
            self._lade_aktiv = False

            self.berechne_gesamtzeit_fuer_zeile(item.row())
            self.aktualisiere_summenanzeige()
            self.speichere_datei()
            return

        if spalte in [0, 7]:
            self.speichere_datei()

    def normalisiere_zeitfeld(self, item):
        text = item.text().strip()
        if not text:
            return

        try:
            teile = text.split(":")
            if len(teile) == 2:
                stunde = int(teile[0])
                minute = int(teile[1])
                if 0 <= stunde <= 23 and 0 <= minute <= 59:
                    item.setText(f"{stunde:02d}:{minute:02d}")
        except Exception:
            pass

    def zeit_zu_minuten(self, zeittext):
        if not zeittext:
            return None

        try:
            stunde, minute = zeittext.strip().split(":")
            return int(stunde) * 60 + int(minute)
        except Exception:
            return None

    def minuten_zu_hhmm(self, minuten):
        if minuten is None or minuten < 0:
            return ""

        stunden = minuten // 60
        rest_minuten = minuten % 60
        return f"{stunden:02d}:{rest_minuten:02d}"

    def berechne_gesamtzeit_fuer_zeile(self, zeile):
        start = self.zelltext(zeile, 2)
        pause_anfang = self.zelltext(zeile, 3)
        pause_ende = self.zelltext(zeile, 4)
        ende = self.zelltext(zeile, 5)

        start_min = self.zeit_zu_minuten(start)
        pause_anfang_min = self.zeit_zu_minuten(pause_anfang)
        pause_ende_min = self.zeit_zu_minuten(pause_ende)
        ende_min = self.zeit_zu_minuten(ende)

        gesamt = ""

        if start_min is not None and ende_min is not None and ende_min >= start_min:
            arbeitszeit = ende_min - start_min

            if (
                pause_anfang_min is not None
                and pause_ende_min is not None
                and pause_ende_min >= pause_anfang_min
            ):
                arbeitszeit -= pause_ende_min - pause_anfang_min

            if arbeitszeit >= 0:
                gesamt = self.minuten_zu_hhmm(arbeitszeit)

        item = self.tabelle.item(zeile, 6)
        if item is None:
            item = QTableWidgetItem("")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tabelle.setItem(zeile, 6, item)

        self._lade_aktiv = True
        item.setText(gesamt)
        self._lade_aktiv = False

    def berechne_gesamtsummen(self):
        ho_minuten = 0
        vorort_minuten = 0

        for zeile in range(self.tabelle.rowCount()):
            minuten = self.zeit_zu_minuten(self.zelltext(zeile, 6))
            if minuten is None:
                continue

            combo = self.tabelle.cellWidget(zeile, 1)
            ort = combo.currentText().strip() if combo else "Vor Ort"

            if ort == "HO":
                ho_minuten += minuten
            else:
                vorort_minuten += minuten

        return ho_minuten, vorort_minuten

    def aktualisiere_summenanzeige(self):
        ho_minuten, vorort_minuten = self.berechne_gesamtsummen()
        gesamt_minuten = ho_minuten + vorort_minuten

        self.ho_label.setText(f"Gesamt HO: {self.minuten_zu_hhmm(ho_minuten)}")
        self.vorort_label.setText(f"Gesamt Vor Ort: {self.minuten_zu_hhmm(vorort_minuten)}")
        self.gesamt_label.setText(f"Gesamt Alles: {self.minuten_zu_hhmm(gesamt_minuten)}")

    def zelltext(self, zeile, spalte):
        item = self.tabelle.item(zeile, spalte)
        return item.text().strip() if item else ""

    @staticmethod
    def datum_to_file(datum_text):
        dt = datetime.strptime(datum_text, "%d.%m.%Y")
        return f"{dt.year}.{dt.month}.{dt.day}"

    @staticmethod
    def datum_from_file(datum_text):
        jahr, monat, tag = map(int, datum_text.split("."))
        return f"{tag:02d}.{monat:02d}.{jahr}"

    def ort_app_to_file(self, ort_text):
        return "HO" if ort_text == "HO" else ""

    def ort_file_to_app(self, ort_text):
        return "HO" if ort_text.strip() == "HO" else "Vor Ort"

    def format_block(self, start, ende):
        start = start.strip()
        ende = ende.strip()

        if start and ende:
            return f"{start}-{ende}"
        if start:
            return f"{start}-"
        if ende:
            return f"-{ende}"
        return ""

    def parse_block(self, block_text):
        block_text = block_text.strip()
        if not block_text:
            return "", ""

        if "-" in block_text:
            a, b = block_text.split("-", 1)
            return a.strip(), b.strip()

        return block_text, ""

    def parse_line(self, line):
        teile = line.rstrip("\n").split("\t")

        while len(teile) < 6:
            teile.append("")

        datum_raw = teile[0].strip()
        ort_raw = teile[1].strip()
        block1 = teile[2].strip()
        block2 = teile[3].strip()
        taetigkeit = teile[5].strip()

        try:
            datum = self.datum_from_file(datum_raw) if datum_raw else ""
        except Exception:
            datum = datum_raw

        ort = self.ort_file_to_app(ort_raw)

        if block1 and not block2:
            start, ende = self.parse_block(block1)
            pause_anfang = ""
            pause_ende = ""
        else:
            start, pause_anfang = self.parse_block(block1)
            pause_ende, ende = self.parse_block(block2)

        return [datum, ort, start, pause_anfang, pause_ende, ende, "", taetigkeit]

    def format_line(self, werte):
        datum, ort, start, pause_anfang, pause_ende, ende, gesamt, text = werte

        datum_file = self.datum_to_file(datum) if datum else ""
        ort_file = self.ort_app_to_file(ort)

        if start and ende and not pause_anfang and not pause_ende:
            block1 = f"{start}-{ende}"
            block2 = ""
        else:
            block1 = self.format_block(start, pause_anfang)
            block2 = self.format_block(pause_ende, ende)

        gesamt = gesamt.strip()
        text = text.replace("\t", " ").replace("\n", " ").strip()

        return "\t".join([datum_file, ort_file, block1, block2, gesamt, text])

    def lade_datei(self):
        self._lade_aktiv = True
        self.tabelle.setRowCount(0)

        if not os.path.exists(self.DATEINAME):
            self._lade_aktiv = False
            self.aktualisiere_summenanzeige()
            return

        try:
            with open(self.DATEINAME, "r", encoding="utf-8") as f:
                zeilen = f.readlines()

            if len(zeilen) <= 2:
                self._lade_aktiv = False
                self.aktualisiere_summenanzeige()
                return

            for line in zeilen[2:]:
                if not line.strip():
                    continue

                werte = self.parse_line(line)
                if not werte:
                    continue

                row = self.tabelle.rowCount()
                self.tabelle.insertRow(row)

                for col in range(len(self.SPALTEN)):
                    if col == 1:
                        continue

                    item = QTableWidgetItem(werte[col])

                    if col == 6:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                    self.tabelle.setItem(row, col, item)

                combo = self.erstelle_ort_combobox(werte[1])
                self.tabelle.setCellWidget(row, 1, combo)

                self.berechne_gesamtzeit_fuer_zeile(row)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Datei konnte nicht gelesen werden:\n{e}"
            )

        self._lade_aktiv = False
        self.aktualisiere_summenanzeige()

    def speichere_datei(self):
        try:
            ho_minuten, vorort_minuten = self.berechne_gesamtsummen()

            with open(self.DATEINAME, "w", encoding="utf-8") as f:
                f.write(
                    f"Summe HO:\t{self.minuten_zu_hhmm(ho_minuten)}\t"
                    f"Summe Vor Ort:\t{self.minuten_zu_hhmm(vorort_minuten)}\n"
                )
                f.write("Datum\tOrt\tBlock 1\tBlock 2\tGesamtzeit\tTätigkeiten\n")

                for row in range(self.tabelle.rowCount()):
                    datum = self.zelltext(row, 0)
                    combo = self.tabelle.cellWidget(row, 1)
                    ort = combo.currentText().strip() if combo else "Vor Ort"
                    start = self.zelltext(row, 2)
                    pause_anfang = self.zelltext(row, 3)
                    pause_ende = self.zelltext(row, 4)
                    ende = self.zelltext(row, 5)
                    gesamt = self.zelltext(row, 6)
                    text = self.zelltext(row, 7)

                    werte = [
                        datum,
                        ort,
                        start,
                        pause_anfang,
                        pause_ende,
                        ende,
                        gesamt,
                        text,
                    ]

                    if any([datum, start, pause_anfang, pause_ende, ende, text]):
                        f.write(self.format_line(werte) + "\n")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Datei konnte nicht gespeichert werden:\n{e}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AktivitaetenTracker()
    window.show()
    sys.exit(app.exec_())

