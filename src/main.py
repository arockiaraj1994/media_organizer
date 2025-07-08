import os
import shutil
from datetime import datetime
from pathlib import Path
import mimetypes
from PIL import Image
from PIL.ExifTags import TAGS
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit,
    QCheckBox, QComboBox, QProgressBar, QDialog, QHBoxLayout
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

class OrganizerWorker(QThread):
    progress = Signal(int)
    log = Signal(str)
    done = Signal(dict)
    progress = Signal(int)
    log = Signal(str)

    def __init__(self, source, dest, structure, dry_run, get_file_date_fn, build_path_fn):
        super().__init__()
        self.source = source
        self.dest = dest
        self.structure = structure
        self.dry_run = dry_run
        self.get_file_date = get_file_date_fn
        self.build_structure_path = build_path_fn

    def run(self):
        copied = 0
        skipped = 0
        errors = 0
        uncategorized = 0
        copied = 0
        skipped = 0
        errors = 0
        all_files = []
        for root, _, files in os.walk(self.source):
            for file in files:
                all_files.append(os.path.join(root, file))

        total = len(all_files)
        if total == 0:
            self.log.emit("No files found to organize.")
            return

        stats = {
            'total': total,
            'copied': copied,
            'skipped': skipped,
            'errors': errors,
            'uncategorized': uncategorized
        }
        self.done.emit(stats)

        for i, file_path in enumerate(all_files):
            try:
                date = self.get_file_date(file_path)
                if date:
                    target_dir = self.build_structure_path(self.dest, date, self.structure)
                else:
                    target_dir = os.path.join(self.dest, "uncategorized")
                    uncategorized += 1
                os.makedirs(target_dir, exist_ok=True)
                dest_file = os.path.join(target_dir, os.path.basename(file_path))

                if not os.path.exists(dest_file):
                    if self.dry_run:
                        self.log.emit(f"[Dry Run] Would copy: {file_path} -> {dest_file}")
                    else:
                        shutil.copy2(file_path, dest_file)
                        self.log.emit(f"Copied: {file_path} -> {dest_file}")
                        copied += 1
                else:
                    self.log.emit(f"Skipped (already exists): {dest_file}")
                    skipped += 1
            except Exception as e:
                self.log.emit(f"Error: {file_path} - {e}")
                errors += 1

            self.progress.emit(int((i + 1) / total * 100))

from PySide6.QtWidgets import QStackedLayout, QHBoxLayout, QListWidget, QListWidgetItem, QSplitter

class MediaOrganizer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Organizer")
        self.setFixedSize(600, 600)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        self.stack = QStackedLayout(self)

        # --- Start Window ---
        self.start_widget = QWidget()
        self.start_layout = QVBoxLayout(self.start_widget)
        self.start_label = QLabel("What would you like to do?")
        self.start_label.setAlignment(Qt.AlignCenter)
        self.start_layout.addWidget(self.start_label)
        self.start_organize_btn = QPushButton("Organize Files")
        self.start_organize_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.organize_widget))
        self.start_layout.addWidget(self.start_organize_btn)
        self.start_duplicate_btn = QPushButton("Find Duplicates")
        self.start_duplicate_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.duplicate_widget))
        self.start_layout.addWidget(self.start_duplicate_btn)
        self.stack.addWidget(self.start_widget)

        # --- Organize Window ---
        self.organize_widget = QWidget()
        self.organize_layout = QVBoxLayout(self.organize_widget)
        self.logo = QLabel()
        self.logo.setPixmap(QPixmap("logo.png").scaledToHeight(100, Qt.SmoothTransformation))
        self.logo.setAlignment(Qt.AlignCenter)
        self.organize_layout.addWidget(self.logo)
        self.label = QLabel("Organize your photos/videos by date")
        self.label.setAlignment(Qt.AlignCenter)
        self.organize_layout.addWidget(self.label)
        self.source_button = QPushButton("Select Source Folder")
        self.source_button.clicked.connect(self.select_source)
        self.organize_layout.addWidget(self.source_button)
        self.dest_button = QPushButton("Select Destination Folder")
        self.dest_button.clicked.connect(self.select_destination)
        self.organize_layout.addWidget(self.dest_button)
        self.structure_label = QLabel("Select Folder Structure:")
        self.organize_layout.addWidget(self.structure_label)
        self.structure_combo = QComboBox()
        self.structure_combo.addItems(["yyyy", "yyyy/MMM", "yyyy/MMM/dd"])
        self.organize_layout.addWidget(self.structure_combo)
        self.dry_run_checkbox = QCheckBox("Dry Run (Don't move files)")
        self.organize_layout.addWidget(self.dry_run_checkbox)
        self.organize_button = QPushButton("Start Organizing")
        self.organize_button.clicked.connect(self.organize_files)
        self.organize_layout.addWidget(self.organize_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.organize_layout.addWidget(self.progress_bar)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.organize_layout.addWidget(self.output)
        self.back_from_organize = QPushButton("Back")
        self.back_from_organize.clicked.connect(lambda: self.stack.setCurrentWidget(self.start_widget))
        self.organize_layout.addWidget(self.back_from_organize)
        self.stack.addWidget(self.organize_widget)

        # --- Duplicate Window ---
        self.duplicate_widget = QWidget()
        self.duplicate_layout = QVBoxLayout(self.duplicate_widget)
        self.dup_instruction_label = QLabel("Select a single folder to scan for duplicate files (by name and size):")
        self.duplicate_layout.addWidget(self.dup_instruction_label)
        self.dup_select_button = QPushButton("Select Folder to Scan for Duplicates")
        self.dup_select_button.clicked.connect(self.select_duplicate_folder)
        self.duplicate_layout.addWidget(self.dup_select_button)
        self.dup_result_list = QListWidget()
        self.dup_result_list.itemClicked.connect(self.handle_duplicate_selection)
        self.duplicate_layout.addWidget(self.dup_result_list)
        self.dup_output = QTextEdit()
        self.dup_output.setReadOnly(True)
        self.duplicate_layout.addWidget(self.dup_output)
        self.clean_now_button = QPushButton("Clean Now (Delete Duplicates)")
        self.clean_now_button.clicked.connect(self.clean_now)
        self.duplicate_layout.addWidget(self.clean_now_button)
        self.move_to_button = QPushButton("Move To (Move Duplicates)")
        self.move_to_button.clicked.connect(self.move_duplicates_to_folder)
        self.duplicate_layout.addWidget(self.move_to_button)
        self.back_from_duplicate = QPushButton("Back")
        self.back_from_duplicate.clicked.connect(lambda: self.stack.setCurrentWidget(self.start_widget))
        self.duplicate_layout.addWidget(self.back_from_duplicate)
        self.stack.addWidget(self.duplicate_widget)

        self.source_dir = ""
        self.dest_dir = ""
        self.not_duplicates = set()  # Store pairs marked as not duplicates
        self.setLayout(self.stack)
        self.stack.setCurrentWidget(self.start_widget)

    def log(self, message):
        if self.stack.currentWidget() == self.organize_widget:
            self.output.append(message)
        elif self.stack.currentWidget() == self.duplicate_widget:
            self.dup_output.append(message)

    def select_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_dir = folder
            self.log(f"Selected Source: {folder}")

    def select_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_dir = folder
            self.log(f"Selected Destination: {folder}")

    def get_exif_date(self, file_path):
        try:
            img = Image.open(file_path)
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'DateTimeOriginal':
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        except:
            return None
        return None

    def get_file_date(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('image'):
            exif_date = self.get_exif_date(file_path)
            if exif_date:
                return exif_date
        ts = os.path.getmtime(file_path)
        return datetime.fromtimestamp(ts)

    def build_structure_path(self, base_dir, date, structure):
        if structure == "yyyy":
            return os.path.join(base_dir, date.strftime('%Y'))
        elif structure == "yyyy/MMM":
            return os.path.join(base_dir, date.strftime('%Y'), date.strftime('%b'))
        elif structure == "yyyy/MMM/dd":
            return os.path.join(base_dir, date.strftime('%Y'), date.strftime('%b'), date.strftime('%d'))
        else:
            return base_dir

    def select_duplicate_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.log(f"Scanning for duplicates in: {folder}")
            duplicates = self.find_duplicates(folder)
            self.dup_result_list.clear()
            if not duplicates:
                self.log("No duplicate files found.")
            else:
                for dup in duplicates:
                    item = QListWidgetItem(" | ".join(dup))
                    self.dup_result_list.addItem(item)
                self.log(f"Found {len(duplicates)} duplicate file pairs.")

    def find_duplicates(self, folder):
        file_map = {}
        duplicates = []
        for root, _, files in os.walk(folder):
            for file in files:
                path = os.path.join(root, file)
                try:
                    size = os.path.getsize(path)
                    key = (file, size)
                    if key in file_map:
                        duplicates.append((file_map[key], path))
                    else:
                        file_map[key] = path
                except Exception as e:
                    self.log(f"Error reading {path}: {e}")
        return duplicates

    def handle_duplicate_selection(self, item):
        files = item.text().split(" | ")
        dialog = QDialog(self)
        dialog.setWindowTitle("Duplicate Files Side by Side")
        main_layout = QVBoxLayout(dialog)
        file_layout = QHBoxLayout()
        for file_path in files:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and mime_type.startswith('image'):
                label = QLabel()
                pixmap = QPixmap(file_path)
                label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                file_layout.addWidget(label)
            elif mime_type and mime_type.startswith('video'):
                video_layout = QVBoxLayout()
                video_widget = QVideoWidget()
                player = QMediaPlayer()
                audio = QAudioOutput()
                player.setAudioOutput(audio)
                player.setVideoOutput(video_widget)
                player.setSource(file_path)
                player.play()
                video_layout.addWidget(video_widget)
                file_layout.addLayout(video_layout)
            else:
                label = QLabel(f"Cannot preview: {file_path}")
                file_layout.addWidget(label)
        main_layout.addLayout(file_layout)
        # Add Not Duplicate checkbox
        not_dup_checkbox = QCheckBox("Not duplicate")
        main_layout.addWidget(not_dup_checkbox)
        # Store the result if checked
        def on_accept():
            if not_dup_checkbox.isChecked():
                # Store as a frozenset so order doesn't matter
                self.not_duplicates.add(frozenset(files))
                self.log(f"Marked as NOT duplicate: {files[0]} and {files[1]}")
            dialog.accept()
        # Add OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(on_accept)
        main_layout.addWidget(ok_btn)
        dialog.setLayout(main_layout)
        dialog.resize(650, 400)
        dialog.exec()

    def clean_now(self):
        # Delete all duplicate files except those marked as not duplicates
        deleted_count = 0
        skipped_count = 0
        for i in range(self.dup_result_list.count()):
            item = self.dup_result_list.item(i)
            files = item.text().split(" | ")
            pair = frozenset(files)
            if pair in self.not_duplicates:
                skipped_count += 1
                continue
            # Delete the second file in the pair
            try:
                os.remove(files[1])
                self.log(f"Deleted duplicate: {files[1]}")
                deleted_count += 1
            except Exception as e:
                self.log(f"Error deleting {files[1]}: {e}")
        self.log(f"Clean complete. Deleted: {deleted_count}, Skipped: {skipped_count} (marked as not duplicate)")

    def move_duplicates_to_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Move Duplicates")
        if not folder:
            self.log("Move cancelled.")
            return
        moved_count = 0
        skipped_count = 0
        for i in range(self.dup_result_list.count()):
            item = self.dup_result_list.item(i)
            files = item.text().split(" | ")
            pair = frozenset(files)
            if pair in self.not_duplicates:
                skipped_count += 1
                continue
            try:
                dest_path = os.path.join(folder, os.path.basename(files[1]))
                shutil.move(files[1], dest_path)
                self.log(f"Moved duplicate: {files[1]} -> {dest_path}")
                moved_count += 1
            except Exception as e:
                self.log(f"Error moving {files[1]}: {e}")
        self.log(f"Move complete. Moved: {moved_count}, Skipped: {skipped_count} (marked as not duplicate)")

    def organize_files(self):
        if not self.source_dir or not self.dest_dir:
            self.log("Please select both source and destination folders.")
            return

        self.progress_bar.setValue(0)
        self.output.clear()

        self.worker = OrganizerWorker(
            self.source_dir,
            self.dest_dir,
            self.structure_combo.currentText(),
            self.dry_run_checkbox.isChecked(),
            self.get_file_date,
            self.build_structure_path
        )
        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.done.connect(self.show_summary)
        self.worker.start()

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QMessageBox
    app = QApplication(sys.argv)

    window = MediaOrganizer()
    window.stack.setCurrentWidget(window.start_widget)
    window.show()
    app.exec()
