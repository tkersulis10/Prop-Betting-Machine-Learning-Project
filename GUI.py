import sys
from pathlib import Path
from getting_bbref_season_data import Player
from getting_bbref_season_data import Season
from getting_bbref_season_data import Team
from getting_bbref_season_data import Game
import reinforcement_learning_run
import get_prop_bets

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QFormLayout, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QScrollArea, QScrollBar
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QPixmap, QIcon

app = QApplication([])
app.setStyle('Fusion')
app.setStyleSheet(Path('GUI_resources/app_styles.qss').read_text())
window = QWidget()
window.setObjectName('mainWindow')
window.setWindowTitle("NBA Prop Betting Analyzer")
window.setWindowIcon(QIcon('GUI_resources/nba_75_logo.png'))
window.setGeometry(0, 0, 1920, 980)
#welcomeMsg = QLabel("<h1>Welcome to our NBA Prop Bet Analyzer!</h1>", parent=window)
#welcomeMsg.setAlignment(Qt.AlignCenter)
welcomeHeading = QLabel('Welcome to our NBA Prop Bet Analyzer!',
                        alignment=Qt.AlignmentFlag.AlignHCenter)
welcomeHeading.setObjectName('welcomeHeading')
#welcomeMsg.move(60, 15)
#directions1 = QLabel("<h1>First select all of the stats you want to be predicted.</h1>", parent=window)
#directions1.setAlignment(Qt.AlignCenter)
subheading1 = QLabel('First select all of the stats you want to be predicted.',
            alignment=Qt.AlignmentFlag.AlignHCenter)
subheading1.setObjectName('subheading1')
#directions2 = QLabel("<h1>Then, input player to be analyzed and click enter below.</h1>", parent=window)
#directions2.setAlignment(Qt.AlignCenter)
subheading2 = QLabel('Then, input player to be analyzed and click enter below.',
            alignment=Qt.AlignmentFlag.AlignHCenter)
subheading2.setObjectName('subheading2')
#directions.move(60, 100)
input_line = QLineEdit()
input_line.returnPressed.connect(lambda: get_player_model())
#results = QLabel("Results")
result_layout = QGridLayout()

pts_button = QPushButton("Points")
ast_button = QPushButton("Assists")
trb_button = QPushButton("Rebounds")
#pts_button.setStyleSheet("QPushButton" "{" "background-color : lightblue;" "}" "QPushButton::pressed" "{""background-color : blue;"   "}")
#ast_button.setStyleSheet("QPushButton" "{" "background-color : lightblue;" "}" "QPushButton::pressed" "{""background-color : blue;"   "}")
#trb_button.setStyleSheet("QPushButton" "{" "background-color : lightblue;" "}" "QPushButton::pressed" "{""background-color : blue;"   "}")
pts_button.clicked.connect(lambda: select_stat("pts"))
ast_button.clicked.connect(lambda: select_stat("ast"))
trb_button.clicked.connect(lambda: select_stat("trb"))

selected_stats = []
stats_clicked = QLabel("Stats selected: ")
stat_layout = QHBoxLayout()
stat_layout.addWidget(pts_button)
stat_layout.addWidget(ast_button)
stat_layout.addWidget(trb_button)

results = QWidget()
results.setLayout(result_layout)

scrolling = QScrollArea()
scrolling.setWidget(results)
scrolling.setWidgetResizable(True)
scrolling.setFixedHeight(600)

layout = QVBoxLayout()
layout.setAlignment(Qt.AlignTop)
layout.addWidget(welcomeHeading)
layout.addWidget(subheading1)
layout.addWidget(subheading2)
layout.addWidget(QLabel("Enter player's name:"))
layout.addWidget(input_line)
layout.addLayout(stat_layout)
layout.addWidget(stats_clicked)
# layout.addLayout(result_layout)
layout.addWidget(scrolling)

def get_player_model():
    # Clear previous input
    for i in reversed(range(result_layout.count())): 
        removeW = result_layout.itemAt(i).widget()
        result_layout.removeWidget(removeW)
        removeW.setParent(None)

    player_name = input_line.text()
    results = reinforcement_learning_run.run(player_name, selected_stats)
    if results == None:
        result_layout.addWidget(QLabel("Not a valid player's name.\nMake sure to capitalize their first and last names."))
    else:
        row_count = 1
        for stat in results:
            result_layout.addWidget(QLabel(stat[0]), row_count, 0, 1, len(stat[3]) - 1)
            result_layout.addWidget(QLabel("Prop Line:"), row_count + 1, 0, 1, len(stat[3]) - 1)
            result_layout.addWidget(QLabel("Predicted Game Stats:"), row_count + 3, 0, 1, len(stat[3]) - 1)
            result_layout.addWidget(QLabel("Actual Game Stats:"), row_count + 6, 0, 1, len(stat[3]) - 1)
            for i in range(len(stat[3])):
                date = stat[5][i]
                result_layout.addWidget(QLabel(date), 0, i, 1, 1)
            for i in range(len(stat[3])):
                prop_line = get_prop_bets.get_props(player_name, stat[0][-3:], stat[5][i])
                if prop_line == None:
                    result_layout.addWidget(QLabel("Error retrieving data."))
                else:
                    prop_line_string = prop_line[0] + " (" + prop_line[1] + ")"
                    predicted = stat[3][i]
                    actual = stat[4][i]
                    result_layout.addWidget(QLabel(prop_line_string), row_count + 2, i, 1, 1)
                    result_layout.addWidget(QLabel(predicted), row_count + 4, i, 1, 1)
                    result_layout.addWidget(QLabel(actual), row_count + 7, i, 1, 1)
                    image_label = QLabel()
                    correct_label = QLabel()
                    if float(predicted) > float(prop_line[0]):
                        image_pixmap = QPixmap('GUI_resources/green_up_arrow.png')
                        image_label.setPixmap(image_pixmap.scaledToWidth(25))
                        result_layout.addWidget(image_label, row_count + 5, i, 1, 1)
                        if float(actual) >= float(prop_line[0]):
                            correct_image = QPixmap('GUI_resources/green_checkmark.png')
                        else:
                            correct_image = QPixmap('GUI_resources/red_x.png')
                        correct_label.setPixmap(correct_image.scaledToWidth(25))
                        result_layout.addWidget(correct_label, row_count + 8, i, 1, 1)
                    else:
                        image_pixmap = QPixmap('GUI_resources/red_down_arrow.png')
                        image_label.setPixmap(image_pixmap.scaledToWidth(25))
                        result_layout.addWidget(image_label, row_count + 5, i, 1, 1)
                        if float(actual) <= float(prop_line[0]):
                            correct_image = QPixmap('GUI_resources/green_checkmark.png')
                        else:
                            correct_image = QPixmap('GUI_resources/red_x.png')
                        correct_label.setPixmap(correct_image.scaledToWidth(25))
                        result_layout.addWidget(correct_label, row_count + 8, i, 1, 1)
            row_count += 9

def select_stat(stat):
    if stat not in selected_stats:
        selected_stats.append(stat)
        stats_clicked.setText(stats_clicked.text() + stat + ", ")

window.setLayout(layout)
window.show()
sys.exit(app.exec())