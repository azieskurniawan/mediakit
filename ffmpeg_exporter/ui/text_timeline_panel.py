"""
Panel for managing animated text timeline.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QCheckBox, QGroupBox,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from core.media_manager import AnimatedTextItem, AnimatedTextTimeline, OverlayPosition
from ui.animated_text_dialog import AnimatedTextDialog
from ui.bulk_text_sequence_dialog import BulkTextSequenceDialog


class TextTimelinePanel(QWidget):
    """Panel for managing animated text timeline."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # HEADER
        header_group = QGroupBox("📝 Animated Text Timeline")
        header_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 2px solid #0f3460;
                border-radius: 8px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
                margin-top: 10px;
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        header_layout = QVBoxLayout()
        header_group.setLayout(header_layout)
        
        # Enable checkbox
        self._enabled_checkbox = QCheckBox("Enable Multi-Text Timeline")
        self._enabled_checkbox.setChecked(False)
        self._enabled_checkbox.toggled.connect(self._on_enabled_toggle)
        self._enabled_checkbox.setStyleSheet("color: #ccd6f6; font-weight: normal;")
        header_layout.addWidget(self._enabled_checkbox)
        
        # Info
        info_label = QLabel(
            "✨ Add multiple texts with custom timing, fade effects, and positioning.\n"
            "Perfect for titles, captions, chapters, and animated text effects!"
        )
        info_label.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: normal;")
        info_label.setWordWrap(True)
        header_layout.addWidget(info_label)
        
        layout.addWidget(header_group)
        
        # TEXT ITEMS LIST
        list_group = QGroupBox("📋 Text Items")
        list_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)
        
        # Timeline visualization
        self._timeline_view = QListWidget()
        self._timeline_view.setMaximumHeight(250)
        self._timeline_view.setStyleSheet("""
            QListWidget {
                background-color: #0a192f;
                border: 1px solid #233554;
                border-radius: 4px;
                color: #ccd6f6;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #172a45;
                border-left: 3px solid #64ffda;
            }
            QListWidget::item:selected {
                background-color: #0f3460;
                color: #64ffda;
                border-left: 3px solid #ffd700;
            }
            QListWidget::item:hover {
                background-color: #172a45;
            }
        """)
        list_layout.addWidget(self._timeline_view)
        
        # Buttons row 1 - Main actions
        btn_row1 = QHBoxLayout()
        
        # BULK SEQUENCE BUTTON (prominent)
        bulk_seq_btn = QPushButton("🚀 Bulk Sequence (Auto-Loop)")
        bulk_seq_btn.setStyleSheet("""
            QPushButton {
                background-color: #e91e63;
                color: white;
                border: 2px solid #ff6090;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c2185b;
            }
        """)
        bulk_seq_btn.setToolTip("Create multiple texts with one setting - auto-loop until video ends!")
        bulk_seq_btn.clicked.connect(self._bulk_sequence)
        btn_row1.addWidget(bulk_seq_btn)
        
        add_btn = QPushButton("➕ Add Text")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: #64ffda;
                border: 1px solid #64ffda;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(100, 255, 218, 0.2);
            }
        """)
        add_btn.clicked.connect(self._add_text_item)
        btn_row1.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.clicked.connect(self._edit_text_item)
        btn_row1.addWidget(edit_btn)
        
        duplicate_btn = QPushButton("📋 Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_text_item)
        btn_row1.addWidget(duplicate_btn)
        
        remove_btn = QPushButton("🗑️ Remove")
        remove_btn.clicked.connect(self._remove_text_item)
        btn_row1.addWidget(remove_btn)
        
        list_layout.addLayout(btn_row1)
        
        # Quick actions row 2
        btn_row2 = QHBoxLayout()
        
        sort_btn = QPushButton("🔢 Sort by Time")
        sort_btn.setToolTip("Sort all text items by start time")
        sort_btn.clicked.connect(self._sort_by_time)
        btn_row2.addWidget(sort_btn)
        
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self._clear_all)
        btn_row2.addWidget(clear_btn)
        
        list_layout.addLayout(btn_row2)
        
        layout.addWidget(list_group)
        
        # TEMPLATES
        template_group = QGroupBox("⚡ Quick Templates")
        template_group.setStyleSheet("""
            QGroupBox {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 5px;
                font-weight: bold;
                color: #64ffda;
                padding-top: 15px;
            }
        """)
        template_layout = QHBoxLayout()
        template_group.setLayout(template_layout)
        
        template_btn1 = QPushButton("📺 Intro/Outro")
        template_btn1.setToolTip("Add intro text at start and outro at end")
        template_btn1.clicked.connect(lambda: self._apply_template("intro_outro"))
        template_layout.addWidget(template_btn1)
        
        template_btn2 = QPushButton("🎯 Chapters")
        template_btn2.setToolTip("Add chapter titles every 5 minutes")
        template_btn2.clicked.connect(lambda: self._apply_template("chapters"))
        template_layout.addWidget(template_btn2)
        
        template_btn3 = QPushButton("💬 Subtitles")
        template_btn3.setToolTip("Bottom-center style for subtitles")
        template_btn3.clicked.connect(lambda: self._apply_template("subtitles"))
        template_layout.addWidget(template_btn3)
        
        layout.addWidget(template_group)
        
        layout.addStretch()
    
    def _bulk_sequence(self):
        """Open bulk text sequence dialog."""
        dialog = BulkTextSequenceDialog(self)
        if dialog.exec() == BulkTextSequenceDialog.Accepted:
            items = dialog.get_sequence_items()
            
            if not items:
                QMessageBox.warning(
                    self,
                    "No Texts",
                    "Please enter at least one text in the list!"
                )
                return
            
            # Add all items to timeline
            for item_config in items:
                self._add_item_to_list(item_config)
            
            # Show success message
            QMessageBox.information(
                self,
                "Sequence Generated!",
                f"✅ Successfully generated {len(items)} text items!\n\n"
                f"Total timeline coverage: {self._format_time(items[-1].get_end_time())}\n\n"
                "Tip: Use 'Sort by Time' to organize if needed."
            )
    
    def _add_text_item(self):
        """Add new text item to timeline."""
        dialog = AnimatedTextDialog(self)
        if dialog.exec() == AnimatedTextDialog.Accepted:
            text_config = dialog.get_config()
            self._add_item_to_list(text_config)
    
    def _edit_text_item(self):
        """Edit selected text item."""
        current_item = self._timeline_view.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a text item to edit")
            return
        
        text_config = current_item.data(Qt.UserRole)
        dialog = AnimatedTextDialog(self, text_config)
        
        if dialog.exec() == AnimatedTextDialog.Accepted:
            updated_config = dialog.get_config()
            current_item.setData(Qt.UserRole, updated_config)
            self._update_item_display(current_item, updated_config)
    
    def _duplicate_text_item(self):
        """Duplicate selected text item."""
        current_item = self._timeline_view.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a text item to duplicate")
            return
        
        text_config = current_item.data(Qt.UserRole)
        # Create copy with offset time
        new_config = AnimatedTextItem(
            text=text_config.text + " (Copy)",
            start_time=text_config.start_time + text_config.duration + 5,
            duration=text_config.duration,
            fade_in=text_config.fade_in,
            fade_out=text_config.fade_out,
            font_file=text_config.font_file,
            font_size=text_config.font_size,
            font_color=text_config.font_color,
            position=text_config.position,
            x_offset=text_config.x_offset,
            y_offset=text_config.y_offset,
            shadow=text_config.shadow,
            box=text_config.box
        )
        self._add_item_to_list(new_config)
    
    def _remove_text_item(self):
        """Remove selected text item."""
        current_row = self._timeline_view.currentRow()
        if current_row >= 0:
            self._timeline_view.takeItem(current_row)
    
    def _clear_all(self):
        """Clear all text items."""
        if self._timeline_view.count() == 0:
            return
        
        reply = QMessageBox.question(
            self, "Clear All", 
            "Remove all text items from timeline?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._timeline_view.clear()
    
    def _sort_by_time(self):
        """Sort items by start time."""
        items = []
        for i in range(self._timeline_view.count()):
            item = self._timeline_view.item(i)
            config = item.data(Qt.UserRole)
            items.append(config)
        
        items.sort(key=lambda x: x.start_time)
        
        self._timeline_view.clear()
        for config in items:
            self._add_item_to_list(config)
    
    def _add_item_to_list(self, config: AnimatedTextItem):
        """Add item to list widget."""
        item = QListWidgetItem()
        item.setData(Qt.UserRole, config)
        self._update_item_display(item, config)
        self._timeline_view.addItem(item)
    
    def _update_item_display(self, item: QListWidgetItem, config: AnimatedTextItem):
        """Update item display text."""
        start_time_str = self._format_time(config.start_time)
        end_time_str = self._format_time(config.get_end_time())
        
        # Truncate long text
        display_text = config.text[:25] + "..." if len(config.text) > 25 else config.text
        
        item_text = (
            f"⏱️ {start_time_str} → {end_time_str} | "
            f"📝 \"{display_text}\" | "
            f"↕️ {config.fade_in}s / {config.fade_out}s"
        )
        item.setText(item_text)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _apply_template(self, template_type: str):
        """Apply quick template."""
        if template_type == "intro_outro":
            # Add intro at 0:00
            intro = AnimatedTextItem(
                text="Welcome! 👋",
                start_time=0,
                duration=5,
                fade_in=1.5,
                fade_out=1.5,
                font_size=72,
                position=OverlayPosition.CENTER,
                shadow=True
            )
            self._add_item_to_list(intro)
            
            # Add outro
            outro = AnimatedTextItem(
                text="Thank You! ❤️",
                start_time=300,  # User can adjust
                duration=5,
                fade_in=1.5,
                fade_out=1.5,
                font_size=72,
                position=OverlayPosition.CENTER,
                shadow=True
            )
            self._add_item_to_list(outro)
        
        elif template_type == "chapters":
            # Add chapter titles every 5 minutes
            chapters = [
                "Chapter 1: Introduction",
                "Chapter 2: Main Content",
                "Chapter 3: Tutorial",
                "Chapter 4: Advanced Tips",
                "Chapter 5: Conclusion"
            ]
            for i, chapter_name in enumerate(chapters):
                chapter = AnimatedTextItem(
                    text=chapter_name,
                    start_time=i * 300,  # Every 5 minutes
                    duration=3,
                    fade_in=1.0,
                    fade_out=1.0,
                    font_size=56,
                    position=OverlayPosition.TOP_LEFT,
                    x_offset=30,
                    y_offset=30,
                    shadow=True,
                    box=False
                )
                self._add_item_to_list(chapter)
        
        elif template_type == "subtitles":
            # Example subtitle template
            subtitle = AnimatedTextItem(
                text="Your subtitle text here...",
                start_time=0,
                duration=5,
                fade_in=0.3,
                fade_out=0.3,
                font_size=40,
                position=OverlayPosition.BOTTOM_LEFT,
                x_offset=50,
                y_offset=100,
                box=True,
                box_color="black@0.7",
                shadow=False
            )
            self._add_item_to_list(subtitle)
        
        QMessageBox.information(
            self,
            "Template Applied",
            f"Template '{template_type}' has been added!\n\n"
            "You can now edit each text item by double-clicking or selecting and clicking 'Edit'."
        )
    
    def _on_enabled_toggle(self, checked: bool):
        """Handle enable toggle."""
        self._timeline_view.setEnabled(checked)
    
    def get_settings(self) -> AnimatedTextTimeline:
        """Get current timeline configuration."""
        items = []
        for i in range(self._timeline_view.count()):
            item = self._timeline_view.item(i)
            config = item.data(Qt.UserRole)
            items.append(config)
        
        return AnimatedTextTimeline(
            enabled=self._enabled_checkbox.isChecked(),
            items=items
        )
    
    def set_settings(self, timeline: AnimatedTextTimeline):
        """Set timeline configuration."""
        self._enabled_checkbox.setChecked(timeline.enabled)
        self._timeline_view.clear()
        
        for item_config in timeline.items:
            self._add_item_to_list(item_config)

