import os
import sys
import time
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, QSize, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QComboBox, QSizePolicy,
                             QLineEdit, QFileDialog, QMessageBox)
from PyQt6.QtGui import QImage, QPixmap
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont


# フォントのパス（システムに応じて変更）
FONT_PATH = f"Fonts/msgothic.ttc"

class WebCamRecordApp(QMainWindow):
    # 録画パラメータ変数定義
    dir_path = ""
    fps = 10
    section_time = 30 #単位(分)
    pixel_list = ("SD", "HD")
    fps_list = ("10", "15", "30", "60")

    def __init__(self):
        super().__init__()


        self.setWindowTitle("定点カメラレコーダー")
        self.setGeometry(100, 100, 300, 150)

        # メインウィジェットとレイアウト
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.v_layout = QVBoxLayout(self.central_widget)

        # 1行目の水平レイアウト
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")
        # カメラ選択用のコンボボックス
        self.camera_selector = QComboBox()
        self.horizontalLayout_1.addWidget(self.camera_selector)
        # カメラ接続ボタン
        self.connect_camera_button = QPushButton("カメラ接続")
        self.horizontalLayout_1.addWidget(self.connect_camera_button)
        self.v_layout.addLayout(self.horizontalLayout_1)

        # 出力先フォルダの選択
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        # （横レイアウトの1要素目）
        self.lineEdit_path = QLineEdit()
        self.lineEdit_path.setObjectName("lineEdit_path")
        self.lineEdit_path.setText("保存先フォルダを指定してください")
        self.horizontalLayout_2.addWidget(self.lineEdit_path)
        # （横レイアウトの2要素目）
        self.pushButton_select_path = QPushButton()
        self.pushButton_select_path.setObjectName("pushButton_select_path")
        self.pushButton_select_path.setText("参照...")
        self.pushButton_select_path.clicked.connect(self.open_folder_dialog)
        self.horizontalLayout_2.addWidget(self.pushButton_select_path)
        self.v_layout.addLayout(self.horizontalLayout_2)

        # カメラ画質選択設定
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        # 画質選択用のラベル
        self.label_1 = QLabel()
        self.label_1.setText("画質選択")
        self.horizontalLayout_3.addWidget(self.label_1)
        # 画質選択設定用のコンボボックス
        self.pixel_size_selector = QComboBox()
        self.horizontalLayout_3.addWidget(self.pixel_size_selector)
        self.pixel_size_selector.addItems(self.pixel_list)
        # FPS設定ラベル
        self.label_2 = QLabel()
        self.label_2.setText("FPS設定: ")
        self.horizontalLayout_3.addWidget(self.label_2)
        # FPS設定用コンボボックス
        self.fps_selector = QComboBox()
        self.horizontalLayout_3.addWidget(self.fps_selector)
        self.fps_selector.addItems(self.fps_list)
        # FPS単位ラベル
        self.label_3 = QLabel()
        self.label_3.setText("(fps)")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.v_layout.addLayout(self.horizontalLayout_3)

        # 1ファイルの最大録画時間設定
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        # 画質選択用のラベル
        self.label_4 = QLabel()
        self.label_4.setText("録画ファイルを ")
        self.horizontalLayout_4.addWidget(self.label_4)
        
        self.lineEdit_record_section_time = QLineEdit()
        self.lineEdit_record_section_time.setObjectName("lineEdit_record_section_time")
        self.lineEdit_record_section_time.setText("60")
        self.horizontalLayout_4.addWidget(self.lineEdit_record_section_time)
        
        self.label_5 = QLabel()
        self.label_5.setText("分ごとに分割して録画する")
        self.horizontalLayout_4.addWidget(self.label_5)

        self.v_layout.addLayout(self.horizontalLayout_4)



        # 録画開始ボタン
        self.record_start_button = QPushButton("録画開始")
        self.record_start_button.setObjectName("record_start_button")
        self.v_layout.addWidget(self.record_start_button)
        self.record_start_button.setEnabled(False)  # 録画ボタンは初期状態で無効

        # 録画停止ボタン
        self.record_stop_button = QPushButton("録画停止")
        self.record_stop_button.setObjectName("record_stop_button")
        self.v_layout.addWidget(self.record_stop_button)
        self.record_stop_button.setEnabled(False)  # 停止ボタンは初期状態で無効

        # カメラリストを取得
        self.available_cameras = self.get_available_cameras()
        self.camera_selector.addItems(self.available_cameras)

        # OpenCV関連
        self.camera_index = 0
        self.capture = None
        self.recording = False  # 録画状態フラグ
        self.video_writer = None  # 動画ライターオブジェクト

        # イベント接続
        self.connect_camera_button.clicked.connect(self.conect_camera)
        self.record_start_button.clicked.connect(self.record_video)
        self.record_stop_button.clicked.connect(self.stop_recording)

    def open_folder_dialog(self):
        # フォルダ選択ダイアログを開く
        folder = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if folder:
            self.lineEdit_path.setText(folder)
            self.dir_path = folder


    def get_available_cameras(self):
        """利用可能なカメラを検出"""
        cameras = []
        for i in range(10):  # 最大10台までチェック
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cameras.append(f"カメラ {i}")
                cap.release()
        return cameras

    def conect_camera(self):
        """カメラを選択"""
        self.camera_index = self.camera_selector.currentIndex()
        if self.capture:
            self.capture.release()
        self.record_start_button.setEnabled(True)
        self.connect_camera_button.setEnabled(False)

    def record_video(self):
        self.recording = True
        self.pushButton_select_path.setEnabled(False)
        self.record_start_button.setEnabled(False)
        self.record_stop_button.setEnabled(True)
        
        if not os.path.exists(self.dir_path) and not os.path.isdir(self.dir_path):
            QMessageBox.warning(self, "警告", "有効な保存先フォルダが選択されていません。")
            self.recording = False
            self.pushButton_select_path.setEnabled(True)
            self.connect_camera_button.setEnabled(True)
            self.record_start_button.setEnabled(True)
            self.record_stop_button.setEnabled(False)
            return

        fps=10
        section_time=2
        camera_pixel=[1280, 720]
        # フォーマットして表示
        str_now = datetime.now().strftime('%Y-%m-%d-%H-%M')
        print("現在時刻:", str_now)

        # Webカメラを開く
        self.capture = cv2.VideoCapture(self.camera_index)
        # カメラの解像度を設定
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, camera_pixel[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_pixel[1])

        # 設定が反映されたか確認
        actual_width = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(f"カメラ解像度: {actual_width}x{actual_height}")

        if not self.capture.isOpened():
            print("カメラを開けません")
            return
        # os.makedirs(output_dir, exist_ok=True)
        
        file_no = 1
        section_start_time = time.time()

        interval = 1.0 / fps  # キャプチャ間隔（秒）
        last_capture_time = time.time()

        # 録画ファイルの設定
        output_file = f"mv_{str_now}.mp4"

        outputpath = os.path.join(self.dir_path, output_file)
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v') # MJPEGコーデック
        video = cv2.VideoWriter(outputpath, fourcc, fps, (int(self.capture.get(3)), int(self.capture.get(4))))
        print(f"画像サイズ: {int(self.capture.get(3))}x{int(self.capture.get(4))}, FPS: {fps}")

        # 映像を取得する
        while True:
            now = time.time()
            # 一定時間経過したら新しいファイルに切り替え
            if now - section_start_time >= section_time*60:
                video.release()  # 現在の録画ファイルを閉じる
                file_no += 1
                section_start_time = now
                str_now = datetime.now().strftime('%Y-%m-%d-%H-%M')
                output_file = f"mv_{str_now}.mp4"
                outputpath = os.path.join(self.dir_path, output_file)
                video = cv2.VideoWriter(outputpath, fourcc, fps, (int(self.capture.get(3)), int(self.capture.get(4))))
                print(f"新しい録画ファイルに切り替え: {outputpath}")
            else:
                # 一定間隔でフレームをキャプチャ
                if now - last_capture_time >= interval:
                    time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 現在の日時を取得
                    ret, frame = self.capture.read()  # フレームを読み込む
                    if not ret:
                        break
                    
                    # OpenCVの画像をPillow形式に変換
                    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    # Pillowで日時を描画
                    draw = ImageDraw.Draw(frame_pil)
                    font = ImageFont.truetype(FONT_PATH, 32)  # フォントサイズを指定
                    draw.text((10, 10), time_stamp, font=font, fill=(255, 255, 255))  # 白色で描画
                    # Pillowの画像をOpenCV形式に戻す
                    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

                    video.write(frame)  # フレームを録画ファイルに書き込む
                    last_capture_time = now

                else:
                    continue
            if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q'キーで終了
                break
            if self.recording == False:
                cv2.destroyAllWindows()
                break
            cv2.imshow('Recording...', frame)  # 映像を表示する

        self.capture.release()  # カメラを解放
    
    def stop_recording(self):
        self.connect_camera_button.setEnabled(True)
        self.pushButton_select_path.setEnabled(True)
        self.record_start_button.setEnabled(False)
        self.record_stop_button.setEnabled(False)
        self.recording = False
        print("stopped.")

    def closeEvent(self, event):
        """アプリ終了時にリソースを解放"""
        if self.capture:
            self.capture.release()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WebCamRecordApp()
    window.show()
    sys.exit(app.exec())





# def capture_time_lapse(output_dir, fps=10, section_time=60, camera_pixel=[1280, 720]):
#     # Webカメラを開く
#     cap = cv2.VideoCapture(0)
#     # カメラの解像度を設定
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_pixel[0])
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_pixel[1])

#     # 設定が反映されたか確認
#     actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
#     actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
#     print(f"カメラ解像度: {actual_width}x{actual_height}")

#     if not cap.isOpened():
#         print("カメラを開けません")
#         return
#     os.makedirs(output_dir, exist_ok=True)
    
#     file_no = 1
#     section_start_time = time.time()

#     interval = 1.0 / fps  # キャプチャ間隔（秒）
#     last_capture_time = time.time()

#     # 録画ファイルの設定
#     output_file = f"video_{file_no}.mp4"
#     outputpath = os.path.join(output_dir, output_file)
#     fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v') # MJPEGコーデック
#     video = cv2.VideoWriter(outputpath, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))
#     print(f"画像サイズ: {int(cap.get(3))}x{int(cap.get(4))}, FPS: {fps}")

#     # 映像を取得する
#     while True:
#         now = time.time()
#         # 一定時間経過したら新しいファイルに切り替え
#         if now - section_start_time >= section_time*60:
#             video.release()  # 現在の録画ファイルを閉じる
#             file_no += 1
#             section_start_time = now
#             output_file = f"video_{file_no}.mp4"
#             outputpath = os.path.join(output_dir, output_file)
#             video = cv2.VideoWriter(outputpath, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))
#             print(f"新しい録画ファイルに切り替え: {outputpath}")
#         else:
#             # 一定間隔でフレームをキャプチャ
#             if now - last_capture_time >= interval:
#                 time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 現在の日時を取得
#                 ret, frame = cap.read()  # フレームを読み込む
#                 if not ret:
#                     break
                
#                 # OpenCVの画像をPillow形式に変換
#                 frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#                 # Pillowで日時を描画
#                 draw = ImageDraw.Draw(frame_pil)
#                 font = ImageFont.truetype(FONT_PATH, 32)  # フォントサイズを指定
#                 draw.text((10, 10), time_stamp, font=font, fill=(255, 255, 255))  # 白色で描画
#                 # Pillowの画像をOpenCV形式に戻す
#                 frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

#                 video.write(frame)  # フレームを録画ファイルに書き込む
#                 last_capture_time = now

#             else:
#                 continue
#         if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q'キーで終了
#             break
#         cv2.imshow('Recording...', frame)  # 映像を表示する

#     cap.release()  # カメラを解放
#     cv2.destroyAllWindows()  # ウィンドウを閉じる
#     print(f"録画が完了しました: {outputpath}")

# def main():
#     output_dir = "videos"
#     # 解像度を設定（幅と高さ）
#     camera_pixel = [1280, 720]  # 幅x高さ
#     fps = 10
#     section_time = 1  # 指定時間間隔ごとに新しいフォルダに保存(単位:分)
#     capture_time_lapse(output_dir, fps, section_time, camera_pixel)

# if __name__ == "__main__":
#     main()