import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QHeaderView
)
from PyQt5.QtCore import Qt


class AktivitaetenTracker(QWidget):
    DATEINAME = "Aktivitätenliste.txt"
    SPALTEN = [
        "Datum",
        "Startzeit",
        "Mittagspause Anfang",
        "Mittagspause Ende",
        "Ende",
        "Tätigkeiten",
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aktivitätentracker")
        self.resize(950, 500)

        self._lade_aktiv = False

        self.init_ui()
        self.lade_datei()

    def init_ui(self):
        hauptlayout = QVBoxLayout()

        eingabe_layout = QHBoxLayout()
        label = QLabel("Tätigkeitskommentar:")
        self.taetigkeit_input = QLineEdit()

        self.button = QPushButton("Zeitstempel eintragen")
        self.button.clicked.connect(self.zeitstempel_eintragen)

        eingabe_layout.addWidget(label)
        eingabe_layout.addWidget(self.taetigkeit_input)
        eingabe_layout.addWidget(self.button)

        self.tabelle = QTableWidget()
        self.tabelle.setColumnCount(len(self.SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(self.SPALTEN)
        self.tabelle.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.itemChanged.connect(self.tabelle_geaendert)

        hauptlayout.addLayout(eingabe_layout)
        hauptlayout.addWidget(self.tabelle)
        self.setLayout(hauptlayout)

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

    def neue_zeile_anlegen(self, datum):
        zeile = self.tabelle.rowCount()
        self.tabelle.insertRow(zeile)
        for spalte in range(len(self.SPALTEN)):
            item = QTableWidgetItem("")
            if spalte == 0:
                item.setText(datum)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tabelle.setItem(zeile, spalte, item)
        return zeile

    def naechste_freie_zeitspalte(self, zeile):
        for spalte in range(1, 5):
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
            QMessageBox.information(self, "Hinweis",
                                    "Alle Zeitfelder sind bereits ausgefüllt.")
            return

        self._lade_aktiv = True
        self.tabelle.item(zeile, spalte).setText(zeit)

        if kommentar:
            item = self.tabelle.item(zeile, 5)
            if item and item.text():
                item.setText(item.text() + " | " + kommentar)
            else:
                self.tabelle.setItem(zeile, 5, QTableWidgetItem(kommentar))

        self._lade_aktiv = False
        self.speichere_datei()
        self.taetigkeit_input.clear()

    def tabelle_geaendert(self, item):
        if self._lade_aktiv:
            return
        if item.column() == 5:
            self.speichere_datei()

    # -------------------------
    # DATEIFORMAT LOGIK
    # -------------------------

    @staticmethod
    def datum_to_file(d):
        dt = datetime.strptime(d, "%d.%m.%Y")
        return f"{dt.year}.{dt.month}.{dt.day}"

    @staticmethod
    def datum_from_file(d):
        y, m, d = map(int, d.split("."))
        return f"{d:02d}.{m:02d}.{y}"

    @staticmethod
    def parse_line(line):
        parts = line.split()
        if not parts:
            return None

        datum = AktivitaetenTracker.datum_from_file(parts[0])

        start = pause_start = pause_end = ende = ""
        text = ""

        time_parts = []
        idx = 1

        for i in range(1, len(parts)):
            if "-" in parts[i] or ":" in parts[i]:
                time_parts.append(parts[i])
                idx = i + 1
            else:
                break

        if len(time_parts) >= 1:
            if "-" in time_parts[0]:
                a, b = time_parts[0].split("-")
                start, pause_start = a, b
            else:
                start = time_parts[0]

        if len(time_parts) >= 2:
            if "-" in time_parts[1]:
                a, b = time_parts[1].split("-")
                pause_end, ende = a, b
            else:
                ende = time_parts[1]

        if idx < len(parts):
            text = " ".join(parts[idx:])

        return [datum, start, pause_start, pause_end, ende, text]

    @staticmethod
    def format_line(values):
        datum, start, p_start, p_end, ende, text = values
        datum = AktivitaetenTracker.datum_to_file(datum)

        parts = [datum]

        if start and p_start:
            parts.append(f"{start}-{p_start}")
        elif start:
            parts.append(start)

        if p_end and ende:
            parts.append(f"{p_end}-{ende}")
        elif ende:
            parts.append(ende)

        if text:
            parts.append(text)

        return " ".join(parts)

    # -------------------------

    def lade_datei(self):
        self._lade_aktiv = True
        self.tabelle.setRowCount(0)

        if not os.path.exists(self.DATEINAME):
            self._lade_aktiv = False
            return

        try:
            with open(self.DATEINAME, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    werte = self.parse_line(line)
                    if not werte:
                        continue

                    row = self.tabelle.rowCount()
                    self.tabelle.insertRow(row)

                    for col, val in enumerate(werte):
                        item = QTableWidgetItem(val)
                        if col != 5:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.tabelle.setItem(row, col, item)

        except Exception as e:
            QMessageBox.critical(self, "Fehler",
                                 f"Datei konnte nicht gelesen werden:\n{e}")

        self._lade_aktiv = False

    def speichere_datei(self):
        try:
            with open(self.DATEINAME, "w", encoding="utf-8") as f:
                for row in range(self.tabelle.rowCount()):
                    werte = []
                    for col in range(len(self.SPALTEN)):
                        item = self.tabelle.item(row, col)
                        text = item.text().strip() if item else ""
                        werte.append(text)

                    line = self.format_line(werte)
                    if line.strip():
                        f.write(line + "\n")

        except Exception as e:
            QMessageBox.critical(self, "Fehler",
                                 f"Datei konnte nicht gespeichert werden:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AktivitaetenTracker()
    window.show()
    sys.exit(app.exec_())
   