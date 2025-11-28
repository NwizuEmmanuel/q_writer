# PySide6 Quiz Builder
# Single-file GUI application to create identification and multiple-choice quizzes and save/load as JSON

import json
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QTextEdit, QPushButton,
                               QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QFormLayout,
                               QRadioButton, QButtonGroup, QGroupBox, QFileDialog, QInputDialog, QComboBox)
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMessageBox as MB

class Question:
    def __init__(self, qtype, question, answer, choices=None):
        self.qtype = qtype  # 'identification' or 'multiple_choice'
        self.question = question
        self.answer = answer
        self.choices = choices or []

    def to_dict(self):
        return {
            'type': self.qtype,
            'question': self.question,
            'answer': self.answer,
            'choices': self.choices
        }

    @staticmethod
    def from_dict(d):
        return Question(d.get('type', 'identification'), d.get('question', ''), d.get('answer', ''), d.get('choices', []))

# Removed enhanced styling

class QuizBuilder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Quiz Builder')
        self.resize(980, 620)
        self.questions = []  # list of Question objects

        # Main widgets
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Left: list of questions and controls
        left_box = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.load_selected_question)
        left_box.addWidget(QLabel('Questions'))
        left_box.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton('Add')
        add_btn.clicked.connect(self.add_question_dialog)
        edit_btn = QPushButton('Edit')
        edit_btn.clicked.connect(self.edit_selected_question)
        remove_btn = QPushButton('Remove')
        remove_btn.clicked.connect(self.remove_selected_question)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(remove_btn)
        left_box.addLayout(btn_layout)

        file_layout = QHBoxLayout()
        load_btn = QPushButton('Load')
        load_btn.clicked.connect(self.load_from_file)
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_to_file)
        file_layout.addWidget(load_btn)
        file_layout.addWidget(save_btn)
        left_box.addLayout(file_layout)

        main_layout.addLayout(left_box, 35)

        # Right: editor form for the selected question
        right_box = QVBoxLayout()
        right_box.addWidget(QLabel('Question Editor'))

        form = QFormLayout()
        # Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(['identification', 'multiple_choice'])
        self.type_combo.currentTextChanged.connect(self.on_type_change)
        form.addRow('Type:', self.type_combo)

        # Question text
        self.question_edit = QTextEdit()
        self.question_edit.setFixedHeight(80)
        form.addRow('Question:', self.question_edit)

        # Identification answer
        self.ident_answer = QLineEdit()
        form.addRow('Answer (identification):', self.ident_answer)

        # Multiple choice area
        self.mc_group = QGroupBox('Multiple Choice')
        mc_layout = QVBoxLayout()
        self.mc_choice_edits = []
        self.mc_choice_radios = QButtonGroup(self)
        for i in range(4):
            h = QHBoxLayout()
            edt = QLineEdit()
            edt.setPlaceholderText(f'Choice {i+1}')
            self.mc_choice_edits.append(edt)
            radio = QRadioButton()
            self.mc_choice_radios.addButton(radio, i)
            h.addWidget(radio)
            h.addWidget(edt)
            mc_layout.addLayout(h)
        self.mc_group.setLayout(mc_layout)
        form.addRow(self.mc_group)

        right_box.addLayout(form)

        # Save edits to selected question
        save_edit_btn = QPushButton('Apply to Selected')
        save_edit_btn.clicked.connect(self.apply_edits_to_selected)
        right_box.addWidget(save_edit_btn)

        # Spacer + preview
        preview_label = QLabel('Preview (JSON for selected)')
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        right_box.addWidget(preview_label)
        right_box.addWidget(self.preview, 1)

        main_layout.addLayout(right_box, 65)

        # initial UI state
        self.on_type_change(self.type_combo.currentText())

    @Slot()
    def add_question_dialog(self):
        # Prompt for type then open an editor pre-filled with a blank question
        items = ('identification', 'multiple_choice')
        typ, ok = QInputDialog.getItem(self, 'Add Question', 'Select type:', items, 0, False)
        if not ok:
            return
        q = Question(typ, '', '' , [])
        self.questions.append(q)
        self.refresh_list()
        self.list_widget.setCurrentRow(len(self.questions)-1)

    @Slot()
    def edit_selected_question(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.questions):
            QMessageBox.information(self, 'No selection', 'Please select a question to edit.')
            return
        # The editor already loads selection; just focus on editor
        self.question_edit.setFocus()

    @Slot()
    def remove_selected_question(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.questions):
            QMessageBox.information(self, 'No selection', 'Please select a question to remove.')
            return
        confirm = QMessageBox.question(self, 'Remove', 'Delete selected question?', MB.StandardButton.Yes | MB.StandardButton.No)
        if confirm == MB.StandardButton.Yes:
            del self.questions[row]
            self.refresh_list()
            self.preview.clear()

    def refresh_list(self):
        self.list_widget.clear()
        for i, q in enumerate(self.questions):
            text = f"{i+1}. [{q.qtype}] {q.question[:60]}"
            item = QListWidgetItem(text)
            self.list_widget.addItem(item)

    @Slot(int)
    def load_selected_question(self, row):
        if row < 0 or row >= len(self.questions):
            # clear editor
            self.question_edit.clear()
            self.ident_answer.clear()
            for edt in self.mc_choice_edits:
                edt.clear()
            self.mc_choice_radios.setExclusive(False)
            for btn in self.mc_choice_radios.buttons():
                btn.setChecked(False)
            self.mc_choice_radios.setExclusive(True)
            self.preview.clear()
            return
        q = self.questions[row]
        self.type_combo.setCurrentText(q.qtype)
        self.question_edit.setPlainText(q.question)
        if q.qtype == 'identification':
            self.ident_answer.setText(q.answer)
        else:
            # assume choices exist
            for i in range(4):
                if i < len(q.choices):
                    self.mc_choice_edits[i].setText(q.choices[i])
                else:
                    self.mc_choice_edits[i].setText('')
            # select radio that matches the answer (by text match)
            self.mc_choice_radios.setExclusive(False)
            for i, btn in enumerate(self.mc_choice_radios.buttons()):
                btn.setChecked(False)
                if i < len(q.choices) and q.choices[i] == q.answer:
                    btn.setChecked(True)
            self.mc_choice_radios.setExclusive(True)

        # show JSON preview for selected question
        self.preview.setPlainText(json.dumps(q.to_dict(), indent=4))

    @Slot()
    def apply_edits_to_selected(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self.questions):
            QMessageBox.information(self, 'No selection', 'Select a question first (or Add one).')
            return
        qtype = self.type_combo.currentText()
        text = self.question_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, 'Missing', 'Question text cannot be empty.')
            return
        if qtype == 'identification':
            ans = self.ident_answer.text().strip()
            if not ans:
                QMessageBox.warning(self, 'Missing', 'Please provide the correct answer for identification.')
                return
            q = Question('identification', text, ans, [])
        else:
            choices = [edt.text().strip() for edt in self.mc_choice_edits if edt.text().strip() != '']
            if len(choices) < 2:
                QMessageBox.warning(self, 'Missing', 'Multiple-choice needs at least 2 choices (enter them in the Choice boxes).')
                return
            # find which radio is selected; fallback to first choice
            selected_id = None
            for btn in self.mc_choice_radios.buttons():
                if btn.isChecked():
                    selected_id = self.mc_choice_radios.id(btn)
                    break
            if selected_id is None or selected_id >= len(choices):
                # If no radio selected or it points outside the provided choices, ask user to pick answer by text
                ans_text, ok = QInputDialog.getItem(self, 'Select Answer', 'Choose the correct answer:', choices, 0, False)
                if not ok:
                    return
                answer = ans_text
            else:
                # if there are blank choices removed we must map selected_id to existing choices by index
                # we'll assume ordering remains; choose by position among non-empty edits
                answer = choices[selected_id]
            q = Question('multiple_choice', text, answer, choices)

        self.questions[row] = q
        self.refresh_list()
        self.list_widget.setCurrentRow(row)
        self.preview.setPlainText(json.dumps(q.to_dict(), indent=4))

    @Slot(str)
    def on_type_change(self, text):
        is_ident = text == 'identification'
        self.ident_answer.setVisible(is_ident)
        self.mc_group.setVisible(not is_ident)

    @Slot()
    def save_to_file(self):
        if not self.questions:
            QMessageBox.information(self, 'Empty', 'No questions to save.')
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save Quiz', 'quiz.json', 'JSON files (*.json)')
        if not path:
            return
        data = [q.to_dict() for q in self.questions]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, 'Saved', f'Saved {len(self.questions)} question(s) to {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save: {e}')

    @Slot()
    def load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Load Quiz', '', 'JSON files (*.json);;All files (*.*)')
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            loaded = []
            for d in data:
                loaded.append(Question.from_dict(d))
            self.questions = loaded
            self.refresh_list()
            if self.questions:
                self.list_widget.setCurrentRow(0)
            QMessageBox.information(self, 'Loaded', f'Loaded {len(self.questions)} question(s) from {path}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load: {e}')
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Unsaved Changes',
                                     'Do you want to save your quiz before exiting?',
                                     MB.StandardButton.Yes | MB.StandardButton.No | MB.StandardButton.Cancel)
        if reply == MB.StandardButton.Yes:
            self.save_to_file()
            event.accept()
        elif reply == MB.StandardButton.No:
            event.accept()
        else:
            event.ignore()
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = QuizBuilder()
    w.show()
    sys.exit(app.exec())
