import os
import shutil
import time
import sys
import bpy
from PyQt5.QtWidgets import QApplication,QProgressDialog,QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QSpacerItem, QSizePolicy, QHBoxLayout, QRadioButton,QStackedWidget
from PyQt5.QtGui import QPixmap 
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from qt_material import apply_stylesheet
import qtawesome as qta
image_path= ""

def make_blender_ready(blender_file_path,selected_image_path):    
    bpy.ops.wm.open_mainfile(filepath=blender_file_path)
    bpy.ops.ptcache.bake_all(bake=True)
    obj = bpy.data.objects.get("demo for blender")
    if obj is not None:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
    else:
        print("Object 'demo for blender' not found.")

    material = bpy.data.materials.new(name="MyMaterial")

    texture = bpy.data.textures.new(name="MyTexture", type='IMAGE')

    image = bpy.data.images.load(selected_image_path)

    texture.image = image
    
    material.use_nodes = True
    nodes = material.node_tree.nodes
    node = nodes.get("Principled BSDF")
    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = image
    material.node_tree.links.new(tex_node.outputs["Color"], node.inputs["Base Color"])

    obj.data.materials[0] = material

def render_image(blender_file_path,selected_image_path,effect_name):

    bpy.ops.wm.read_homefile(use_empty=True)
    make_blender_ready(blender_file_path,selected_image_path)
    
    output_directory = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_directory, "temp.png")

    if(effect_name == "Curved"):
        bpy.ops.object.shade_smooth(use_auto_smooth=True)
    
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.filepath = output_path

    render_result = bpy.ops.render.render(write_still=True)
    if render_result == {'FINISHED'}:
        print("Rendering completed successfully.")
    else:
        print("Rendering failed.")

    return output_path
    

class StackedWidget(QStackedWidget):
    switch_screen_signal = pyqtSignal(int, QPixmap)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.effects_screen = None

    def switch_screen(self, index, image=None):
        self.setCurrentIndex(index)
        if self.effects_screen is not None and image is not None:
            self.effects_screen.set_image(image)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSG19VIT Tool to generate Synthetically warped Document Images")
        self.setGeometry(500, 150, 600, 600)  

        self.setStyleSheet("background-color: #303035;")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.stacked_widget = StackedWidget(self.central_widget)
        self.main_layout.addWidget(self.stacked_widget)

        self.upload_screen = UploadScreen()
        self.effects_screen = EffectsScreen()
        self.stacked_widget.effects_screen = self.effects_screen

        self.stacked_widget.addWidget(self.upload_screen)
        self.stacked_widget.addWidget(self.effects_screen)

        self.stacked_widget.switch_screen_signal.connect(self.stacked_widget.switch_screen)
        self.stacked_widget.switch_screen_signal[int, QPixmap].connect(self.switch_screen)

        self.stacked_widget.switch_screen(0,None)

        self.adjustSize()

    def switch_screen(self, index, image=None):
        self.stacked_widget.setCurrentIndex(index)
        

class UploadScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.layout.addWidget(self.image_label)
        self.image_label.setMinimumSize(500, 500)  
        self.image_label.setText("Your Uploaded Image will be displayed here.")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                font-size: 20px; /* Increase the font size */
                border 1px solid #28282B; /* Add a border */
            }
        """)

        global image_path

        spacer = QSpacerItem(5, 10, QSizePolicy.Minimum)
        self.layout.addSpacerItem(spacer)
        
        
        self.button_layout = QVBoxLayout()
        self.layout.addLayout(self.button_layout)

        fa5_icon = qta.icon('fa5s.upload', color='white',scalefactor=0.5)        
        self.upload_button = QPushButton(" Upload Image")
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;                
                color: #FFFFFF;
            }
        """)
        self.upload_button.setIcon(fa5_icon)
        self.upload_button.setIconSize(QSize(15, 15))
        self.upload_button.clicked.connect(self.upload_image)
        self.button_layout.addWidget(self.upload_button)

        fa5_icon = qta.icon('fa5s.exchange-alt', color='white',scalefactor=0.5)
        self.change_button = QPushButton(" Change Image")
        self.change_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
            }""")
        self.change_button.setIcon(fa5_icon)
        self.change_button.setIconSize(QSize(15, 15))
        self.change_button.setVisible(False)
        self.change_button.clicked.connect(self.change_image)
        self.button_layout.addWidget(self.change_button)

        spacer = QSpacerItem(20, 0, QSizePolicy.Minimum)
        self.button_layout.addSpacerItem(spacer)

        fa5_icon = qta.icon('fa5s.magic', color='white',scalefactor=0.5)
        self.apply_button = QPushButton(" Apply Effects")
        self.apply_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
            }""")
        self.apply_button.setIcon(fa5_icon)
        self.apply_button.setIconSize(QSize(15, 15))
        self.apply_button.setVisible(False)
        self.apply_button.clicked.connect(self.apply_effects)
        self.button_layout.addWidget(self.apply_button)

    def set_image(self, pixmap):
        window_size = self.parent().size()
        scaled_pixmap = pixmap.scaled(window_size * 0.5, Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(scaled_pixmap.size())

    def upload_image(self):
        global image_path
        file_dialog = QFileDialog()
        selected_path, _ = file_dialog.getOpenFileName(self, "Select Image")
        if selected_path and selected_path.endswith((".png", ".jpg", ".jpeg")):
            image_path = selected_path
            pixmap = QPixmap(image_path)
            self.set_image(pixmap)
            self.image_label.setText("")
            self.upload_button.setVisible(False)
            self.change_button.setVisible(True)
            self.apply_button.setVisible(True)
        else:
            QMessageBox.critical(self, "Invalid File", "Please select a valid image file.")

    def change_image(self):
        global image_path
        file_dialog = QFileDialog()
        selected_path, _ = file_dialog.getOpenFileName(self, "Select Image")
        if selected_path and selected_path.endswith((".png", ".jpg", ".jpeg")):
            image_path = selected_path
            pixmap = QPixmap(image_path)
            self.set_image(pixmap)
            self.image_label.setText("")
        else:
            QMessageBox.critical(self, "Invalid File", "Please select a valid image file.")

    def apply_effects(self):
        pixmap = self.image_label.pixmap()
        if pixmap:
            self.parent().switch_screen_signal.emit(1, pixmap) 
        else:
            QMessageBox.critical(self, "No Image", "Please upload an image before applying effects.")

class EffectsScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.layout.addWidget(self.image_label)
        self.layout.setAlignment(self.image_label, Qt.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setAcceptDrops(True)
        self.image_label.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.image_label)

        spacer = QSpacerItem(0, 20, QSizePolicy.Minimum)
        self.layout.addSpacerItem(spacer)

        self.effect_options_layout = QHBoxLayout()
        self.layout.addLayout(self.effect_options_layout)

        self.effect_buttons = []

        effect_groups = {
            "Perspective": ["Y-Left","Y-Right", "X-Top","X-Bottom"],
            "Rotation": ["90°","180°","270°","360"],
            "Fold Corners": ["Fold TL","Fold TR","Fold BL","Fold BR","Fold Both Top","Fold Both Right"],
            "Fold Axes" : ["Fold Vertical","Fold Horizontal","Fold Diagonal 1","Fold Diagonal 2"],
            "Crumpled": ["Easy Crumpled 1", "Easy Crumpled 2" , "Hard Crumpled 1","Hard Crumpled 2"],
            "Crease Corners": ["Crease TL","Crease TR","Crease BL","Crease BR","Crease Both Right","Crease Both Left","Crease Both Top","Crease Both Bottom","Crease All Corners"],
            "Crease Axes" : ["Crease Vertical","Crease Multiple Vertical","Crease Horizontal","Crease Multiple Horizontal","Crease Diagonal 1","Crease Diagonal 2","Plus(+)","Cross(X)"],
            "Curled": [ "Curl TL","Curl TR","Curl BL","Curl BR","Curl Both Right","Curl Both Left","Curl Both Top","Curl Both Bottom","Curl All Corners"],
        }

        labels = {
            "Perspective": "Perspective",
            "Rotation": "Rotation",
            "Fold Corners": "Fold Corners",
            "Fold Axes": "Fold Axes",
            "Crumpled": "Crumpled",
            "Crease Corners": "Crease Corners",
            "Crease Axes": "Crease Axes",
            "Curled": "Curled",
        }

        self.label_layout = QVBoxLayout()
        for label in labels.values():
            self.label_layout.addWidget(QLabel(label))
        self.effect_options_layout.addLayout(self.label_layout)

        self.effect_name_layout = QVBoxLayout()
        for label in labels.values():
            group = QHBoxLayout()
            group.setAlignment(Qt.AlignTop) 
            for effect_names in effect_groups[label]:
                effect_button = QRadioButton(effect_names)
                effect_button.toggled.connect(self.effect_button_toggled)
                group.addWidget(effect_button)
            self.effect_name_layout.addLayout(group)
        
        self.effect_options_layout.addLayout(self.effect_name_layout)


        self.save_export_layout = QHBoxLayout()

        # Export to blender Button
        fa5_icon = qta.icon('fa5s.file-export', color='white', scalefactor=0.5)
        self.export_button = QPushButton(" Export to Blender File")
        self.export_button.setVisible(False)
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
            }""")
        self.export_button.clicked.connect(self.export_to_blender)
        self.export_button.setIcon(fa5_icon)
        self.export_button.setIconSize(QSize(15, 15))

        # Save Button
        fa5_icon = qta.icon('fa5s.save', color='white', scalefactor=0.5)
        self.save_button = QPushButton(" Save File as PNG")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
                color: #FFFFFF;
            }""")
        self.save_button.setIcon(fa5_icon)
        self.save_button.setIconSize(QSize(15, 15))
        self.save_button.setVisible(False)
        self.save_button.clicked.connect(self.save_image)

        self.save_export_layout.addWidget(self.save_button)
        spacer = QSpacerItem(15, 15, QSizePolicy.Minimum)
        self.save_export_layout.addSpacerItem(spacer)
        self.save_export_layout.addWidget(self.export_button)
        # add space
        spacer = QSpacerItem(0, 20, QSizePolicy.Minimum)
        self.layout.addSpacerItem(spacer)

        self.layout.addLayout(self.save_export_layout)

        fa5_icon = qta.icon('fa5s.list', color='white', scalefactor=0.5)
        self.render_button = QPushButton(" Render All Effects")
        self.render_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
                color: #FFFFFF;
            }""")
        self.render_button.setIcon(fa5_icon)
        self.render_button.setIconSize(QSize(15, 15))
        self.render_button.clicked.connect(self.render_all_effects)
        self.layout.addWidget(self.render_button)

        self.back_button = QPushButton("Go Back")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #28282B;
                color: #FFFFFF;
                color: #FFFFFF;
            }""")
        self.back_button.setIconSize(QSize(15, 15))
        self.back_button.clicked.connect(self.go_back)
        self.layout.addWidget(self.back_button)

        self.selected_effect = None

    def export_to_blender(self):
        blender_file_path, _ = QFileDialog.getSaveFileName(self, "Export to Blender File", "", "Blender Files (*.blend)")
        if blender_file_path:
            effect_name = self.selected_effect

            # Specify the source Blender preset file path based on the selected effect
            preset_file_path = ""

                       
            if effect_name == "Y-Right":
                preset_file_path = "./warp presets/right.blend"
            elif effect_name == "Y-Left":
                preset_file_path = "./warp presets/left.blend"
            elif effect_name == "X-Top":
                preset_file_path = "./warp presets/top.blend"
            elif effect_name == "X-Bottom":
                preset_file_path = "./warp presets/bottom.blend"
            # Rotation
            elif effect_name == "90°":
                preset_file_path = "./warp presets/90.blend"
            elif effect_name == "180°":
                preset_file_path = "./warp presets/180.blend"
            elif effect_name == "270°":
                preset_file_path = "./warp presets/270.blend"
            elif effect_name == "360":
                preset_file_path = "./warp presets/360.blend"
            # Fold Corners
            elif effect_name == "Fold TL":
                preset_file_path = "./warp presets/fold_tl.blend"
            elif effect_name == "Fold TR":
                preset_file_path = "./warp presets/fold_tr.blend"
            elif effect_name == "Fold BL":
                preset_file_path = "./warp presets/fold_bl.blend"
            elif effect_name == "Fold BR":
                preset_file_path = "./warp presets/fold_br.blend"
            elif effect_name == "Fold Both Right":
                preset_file_path = "./warp presets/fold_both_r.blend"
            elif effect_name == "Fold Both Top":
                preset_file_path = "./warp presets/fold_both_t.blend"
            elif effect_name == "Fold Vertical":
                preset_file_path = "./warp presets/fold_v.blend"
            elif effect_name == "Fold Horizontal":
                preset_file_path = "./warp presets/fold_h.blend"
            elif effect_name == "Fold Diagonal 1":
                preset_file_path = "./warp presets/fold_d1.blend"
            elif effect_name == "Fold Diagonal 2":
                preset_file_path = "./warp presets/fold_d2.blend"
            # Crumpled
            elif effect_name == "Easy Crumpled 1":
                preset_file_path = "./warp presets/easy_crumpled_1.blend"
            elif effect_name == "Easy Crumpled 2":
                preset_file_path = "./warp presets/easy_crumpled_2.blend"
            elif effect_name == "Hard Crumpled 1":
                preset_file_path = "./warp presets/hard_crumpled_1.blend"
            elif effect_name == "Hard Crumpled 2":
                preset_file_path = "./warp presets/hard_crumpled_2.blend"
            # Crease Corners
            elif effect_name == "Crease TL":
                preset_file_path = "./warp presets/crease_tl.blend"
            elif effect_name == "Crease TR":
                preset_file_path = "./warp presets/crease_tr.blend"
            elif effect_name == "Crease BL":
                preset_file_path = "./warp presets/crease_bl.blend"
            elif effect_name == "Crease BR":
                preset_file_path = "./warp presets/crease_br.blend"
            elif effect_name == "Crease Both Right":
                preset_file_path = "./warp presets/crease_both_r.blend"
            elif effect_name == "Crease Both Left":
                preset_file_path = "./warp presets/crease_both_l.blend"
            elif effect_name == "Crease Both Top":
                preset_file_path = "./warp presets/crease_both_t.blend"
            elif effect_name == "Crease Both Bottom":
                preset_file_path = "./warp presets/crease_both_b.blend"
            elif effect_name == "Crease All Corners":
                preset_file_path = "./warp presets/crease_all.blend"
            # Crease Axes
            elif effect_name == "Crease Vertical":
                preset_file_path = "./warp presets/crease_v_single.blend"
            elif effect_name == "Crease Multiple Vertical":
                preset_file_path = "./warp presets/crease_v_multiple.blend"
            elif effect_name == "Crease Horizontal":
                preset_file_path = "./warp presets/crease_h_single.blend"
            elif effect_name == "Crease Multiple Horizontal":
                preset_file_path = "./warp presets/crease_h_multiple.blend"
            elif effect_name == "Crease Diagonal 1":
                preset_file_path = "./warp presets/crease_d1.blend"
            elif effect_name == "Crease Diagonal 2":
                preset_file_path = "./warp presets/crease_d2.blend"
            elif effect_name == "Plus(+)":
                preset_file_path = "./warp presets/crease_plus.blend"
            elif effect_name == "Cross(X)":
                preset_file_path = "./warp presets/crease_cross.blend"                
            # Curled
            elif effect_name == "Curl TL":
                preset_file_path = "./warp presets/curl_tl.blend"
            elif effect_name == "Curl TR":
                preset_file_path = "./warp presets/curl_tr.blend"
            elif effect_name == "Curl BL":
                preset_file_path = "./warp presets/curl_bl.blend"
            elif effect_name == "Curl BR":
                preset_file_path = "./warp presets/curl_br.blend"
            elif effect_name == "Curl Both Right":
                preset_file_path = "./warp presets/curl_both_r.blend"
            elif effect_name == "Curl Both Left":
                preset_file_path = "./warp presets/curl_both_l.blend"
            elif effect_name == "Curl Both Top":
                preset_file_path = "./warp presets/curl_both_t.blend"
            elif effect_name == "Curl Both Bottom":
                preset_file_path = "./warp presets/curl_both_b.blend"
            elif effect_name == "Curl All Corners":
                preset_file_path = "./warp presets/curl_all_corners.blend"


            if preset_file_path:
                try:
                    # Copy the preset file to the selected location
                    shutil.copy(preset_file_path, blender_file_path)
                    QMessageBox.information(self, "Export Successful", "Exported to Blender file: " + blender_file_path)
                except Exception as e:
                    QMessageBox.critical(self, "Export Error", "An error occurred while exporting the file:\n" + str(e))
            else:
                QMessageBox.warning(self, "Export Error", "No preset file path specified for the selected effect.")

    def go_back(self):
        empty_pixmap = QPixmap()
        self.parent().switch_screen_signal.emit(0,empty_pixmap)
    def effect_button_toggled(self):
        effect_button = self.sender()
        if effect_button.isChecked():
            self.selected_effect = effect_button.text()
            self.export_button.setVisible(True)
            if self.selected_effect == "Y-Right":
                blender_file_path = "./warp presets/right.blend"
            elif self.selected_effect == "Y-Left":
                blender_file_path = "./warp presets/left.blend"
            elif self.selected_effect == "X-Top":
                blender_file_path = "./warp presets/top.blend"
            elif self.selected_effect == "X-Bottom":
                blender_file_path = "./warp presets/bottom.blend"
            # Rotation
            elif self.selected_effect == "90°":
                blender_file_path = "./warp presets/90.blend"
            elif self.selected_effect == "180°":
                blender_file_path = "./warp presets/180.blend"
            elif self.selected_effect == "270°":
                blender_file_path = "./warp presets/270.blend"
            elif self.selected_effect == "360":
                blender_file_path = "./warp presets/360.blend"
            # Fold Corners
            elif self.selected_effect == "Fold TL":
                blender_file_path = "./warp presets/fold_tl.blend"
            elif self.selected_effect == "Fold TR":
                blender_file_path = "./warp presets/fold_tr.blend"
            elif self.selected_effect == "Fold BL":
                blender_file_path = "./warp presets/fold_bl.blend"
            elif self.selected_effect == "Fold BR":
                blender_file_path = "./warp presets/fold_br.blend"
            elif self.selected_effect == "Fold Both Right":
                blender_file_path = "./warp presets/fold_both_r.blend"
            elif self.selected_effect == "Fold Both Top":
                blender_file_path = "./warp presets/fold_both_t.blend"
           
            # Fold Axes
            elif self.selected_effect == "Fold Vertical":
                blender_file_path = "./warp presets/fold_v.blend"
            elif self.selected_effect == "Fold Horizontal":
                blender_file_path = "./warp presets/fold_h.blend"
            elif self.selected_effect == "Fold Diagonal 1":
                blender_file_path = "./warp presets/fold_d1.blend"
            elif self.selected_effect == "Fold Diagonal 2":
                blender_file_path = "./warp presets/fold_d2.blend"
            # Crumpled
            elif self.selected_effect == "Easy Crumpled 1":
                blender_file_path = "./warp presets/easy_crumpled_1.blend"
            elif self.selected_effect == "Easy Crumpled 2":
                blender_file_path = "./warp presets/easy_crumpled_2.blend"
            elif self.selected_effect == "Hard Crumpled 1":
                blender_file_path = "./warp presets/hard_crumpled_1.blend"
            elif self.selected_effect == "Hard Crumpled 2":
                blender_file_path = "./warp presets/hard_crumpled_2.blend"
            # Crease Corners
            elif self.selected_effect == "Crease TL":
                blender_file_path = "./warp presets/crease_tl.blend"
            elif self.selected_effect == "Crease TR":
                blender_file_path = "./warp presets/crease_tr.blend"
            elif self.selected_effect == "Crease BL":
                blender_file_path = "./warp presets/crease_bl.blend"
            elif self.selected_effect == "Crease BR":
                blender_file_path = "./warp presets/crease_br.blend"
            elif self.selected_effect == "Crease Both Right":
                blender_file_path = "./warp presets/crease_both_r.blend"
            elif self.selected_effect == "Crease Both Left":
                blender_file_path = "./warp presets/crease_both_l.blend"
            elif self.selected_effect == "Crease Both Top":
                blender_file_path = "./warp presets/crease_both_t.blend"
            elif self.selected_effect == "Crease Both Bottom":
                blender_file_path = "./warp presets/crease_both_b.blend"
            elif self.selected_effect == "Crease All Corners":
                blender_file_path = "./warp presets/crease_all.blend"
            # Crease Axes
            elif self.selected_effect == "Crease Vertical":
                blender_file_path = "./warp presets/crease_v_single.blend"
            elif self.selected_effect == "Crease Multiple Vertical":
                blender_file_path = "./warp presets/crease_v_multiple.blend"
            elif self.selected_effect == "Crease Horizontal":
                blender_file_path = "./warp presets/crease_h_single.blend"
            elif self.selected_effect == "Crease Multiple Horizontal":
                blender_file_path = "./warp presets/crease_h_multiple.blend"
            elif self.selected_effect == "Crease Diagonal 1":
                blender_file_path = "./warp presets/crease_d1.blend"
            elif self.selected_effect == "Crease Diagonal 2":
                blender_file_path = "./warp presets/crease_d2.blend"
            elif self.selected_effect == "Plus(+)":
                blender_file_path = "./warp presets/crease_plus.blend"
            elif self.selected_effect == "Cross(X)":
                blender_file_path = "./warp presets/crease_cross.blend"
            # Curled
            elif self.selected_effect == "Curl TL":
                blender_file_path = "./warp presets/curl_tl.blend"
            elif self.selected_effect == "Curl TR":
                blender_file_path = "./warp presets/curl_tr.blend"
            elif self.selected_effect == "Curl BL":
                blender_file_path = "./warp presets/curl_bl.blend"
            elif self.selected_effect == "Curl BR":
                blender_file_path = "./warp presets/curl_br.blend"
            elif self.selected_effect == "Curl Both Right":
                blender_file_path = "./warp presets/curl_both_r.blend"
            elif self.selected_effect == "Curl Both Left":
                blender_file_path = "./warp presets/curl_both_l.blend"
            elif self.selected_effect == "Curl Both Top":
                blender_file_path = "./warp presets/curl_both_t.blend"
            elif self.selected_effect == "Curl Both Bottom":
                blender_file_path = "./warp presets/curl_both_b.blend"
            elif self.selected_effect == "Curl All Corners":
                blender_file_path = "./warp presets/curl_all_corners.blend"

            output_path = render_image(blender_file_path,image_path,self.selected_effect)
            pixmap = QPixmap(output_path)
            self.set_image(pixmap)
            self.save_button.setVisible(True)
        else:
            self.selected_effect = None
            self.export_button.setVisible(False)
            self.save_button.setVisible(False)


    def save_image(self):
        if self.image_label.pixmap():
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Image", "", "PNG Image (*.png);;All Files (*)"
            )
            if file_path:
                self.image_label.pixmap().save(file_path, "PNG")

    def render_all_effects(self):
        dataset_dir = "dataset"
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
        global image_path
        base_image_path = image_path 
        base_image_name = os.path.basename(base_image_path)
        
        dataset_dir = "dataset"
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)

        effect_names =[ "Y-Left","Y-Right","X-Top","X-Bottom","90°","180°","270°","360","Fold TL","Fold TR","Fold BL","Fold BR","Fold Both Right","Fold Both Left","Fold Both Top","Fold Both Bottom","Fold Vertical","Fold Horizontal","Fold Diagonal 1","Fold Diagonal 2","Easy Crumpled 1", "Easy Crumpled 2" , "Hard Crumpled 1","Hard Crumpled 2","Crease TL","Crease TR","Crease BL","Crease BR","Crease Both Right","Crease Both Left","Crease Both Top","Crease Both Bottom","Crease All Corners","Crease Vertical","Crease Multiple Vertical","Crease Horizontal","Crease Multiple Horizontal","Crease Diagonal 1","Crease Diagonal 2","Plus(+)","Cross(X)","Curl TL","Curl TR","Curl BL","Curl BR","Curl Both Right","Curl Both Left","Curl Both Top","Curl Both Bottom","Curl All Corners"]
        for effect_name in effect_names:

            self.progress_dialog = QProgressDialog("Rendering "+effect_name+" ...", None, 0, 0, self)
            self.progress_dialog.setMinimumSize(300, 100)
            self.progress_dialog.setWindowTitle("Attention")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(False)
            self.progress_dialog.setAutoReset(False)
            self.progress_dialog.show()
            QApplication.processEvents()  
            
            if effect_name == "Y-Right":
                blender_file_path = "./warp presets/right.blend"
            elif effect_name == "Y-Left":
                blender_file_path = "./warp presets/left.blend"
            elif effect_name == "X-Top":
                blender_file_path = "./warp presets/top.blend"
            elif effect_name == "X-Bottom":
                blender_file_path = "./warp presets/bottom.blend"
            # Rotation
            elif effect_name == "90°":
                blender_file_path = "./warp presets/90.blend"
            elif effect_name == "180°":
                blender_file_path = "./warp presets/180.blend"
            elif effect_name == "270°":
                blender_file_path = "./warp presets/270.blend"
            elif effect_name == "360":
                blender_file_path = "./warp presets/360.blend"
            # Fold Corners
            elif effect_name == "Fold TL":
                blender_file_path = "./warp presets/fold_tl.blend"
            elif effect_name == "Fold TR":
                blender_file_path = "./warp presets/fold_tr.blend"
            elif effect_name == "Fold BL":
                blender_file_path = "./warp presets/fold_bl.blend"
            elif effect_name == "Fold BR":
                blender_file_path = "./warp presets/fold_br.blend"
            elif effect_name == "Fold Both Right":
                blender_file_path = "./warp presets/fold_both_r.blend"
            elif effect_name == "Fold Both Top":
                blender_file_path = "./warp presets/fold_both_t.blend"
            elif effect_name == "Fold Vertical":
                blender_file_path = "./warp presets/fold_v.blend"
            elif effect_name == "Fold Horizontal":
                blender_file_path = "./warp presets/fold_h.blend"
            elif effect_name == "Fold Diagonal 1":
                blender_file_path = "./warp presets/fold_d1.blend"
            elif effect_name == "Fold Diagonal 2":
                blender_file_path = "./warp presets/fold_d2.blend"
            # Crumpled
            elif effect_name == "Easy Crumpled 1":
                blender_file_path = "./warp presets/easy_crumpled_1.blend"
            elif effect_name == "Easy Crumpled 2":
                blender_file_path = "./warp presets/easy_crumpled_2.blend"
            elif effect_name == "Hard Crumpled 1":
                blender_file_path = "./warp presets/hard_crumpled_1.blend"
            elif effect_name == "Hard Crumpled 2":
                blender_file_path = "./warp presets/hard_crumpled_2.blend"
            # Crease Corners
            elif effect_name == "Crease TL":
                blender_file_path = "./warp presets/crease_tl.blend"
            elif effect_name == "Crease TR":
                blender_file_path = "./warp presets/crease_tr.blend"
            elif effect_name == "Crease BL":
                blender_file_path = "./warp presets/crease_bl.blend"
            elif effect_name == "Crease BR":
                blender_file_path = "./warp presets/crease_br.blend"
            elif effect_name == "Crease Both Right":
                blender_file_path = "./warp presets/crease_both_r.blend"
            elif effect_name == "Crease Both Left":
                blender_file_path = "./warp presets/crease_both_l.blend"
            elif effect_name == "Crease Both Top":
                blender_file_path = "./warp presets/crease_both_t.blend"
            elif effect_name == "Crease Both Bottom":
                blender_file_path = "./warp presets/crease_both_b.blend"
            elif effect_name == "Crease All Corners":
                blender_file_path = "./warp presets/crease_all.blend"
            # Crease Axes
            elif effect_name == "Crease Vertical":
                blender_file_path = "./warp presets/crease_v_single.blend"
            elif effect_name == "Crease Multiple Vertical":
                blender_file_path = "./warp presets/crease_v_multiple.blend"
            elif effect_name == "Crease Horizontal":
                blender_file_path = "./warp presets/crease_h_single.blend"
            elif effect_name == "Crease Multiple Horizontal":
                blender_file_path = "./warp presets/crease_h_multiple.blend"
            elif effect_name == "Crease Diagonal 1":
                blender_file_path = "./warp presets/crease_d1.blend"
            elif effect_name == "Crease Diagonal 2":
                blender_file_path = "./warp presets/crease_d2.blend"
            elif effect_name == "Plus(+)":
                blender_file_path = "./warp presets/crease_plus.blend"
            elif effect_name == "Cross(X)":
                blender_file_path = "./warp presets/crease_cross.blend"                
            # Curled
            elif effect_name == "Curl TL":
                blender_file_path = "./warp presets/curl_tl.blend"
            elif effect_name == "Curl TR":
                blender_file_path = "./warp presets/curl_tr.blend"
            elif effect_name == "Curl BL":
                blender_file_path = "./warp presets/curl_bl.blend"
            elif effect_name == "Curl BR":
                blender_file_path = "./warp presets/curl_br.blend"
            elif effect_name == "Curl Both Right":
                blender_file_path = "./warp presets/curl_both_r.blend"
            elif effect_name == "Curl Both Left":
                blender_file_path = "./warp presets/curl_both_l.blend"
            elif effect_name == "Curl Both Top":
                blender_file_path = "./warp presets/curl_both_t.blend"
            elif effect_name == "Curl Both Bottom":
                blender_file_path = "./warp presets/curl_both_b.blend"
            elif effect_name == "Curl All Corners":
                blender_file_path = "./warp presets/curl_all_corners.blend"

            timestamp = str(int(time.time()))  
            output_image_name = f"{effect_name}_{timestamp}_output.png"

            output_image_path = os.path.join(dataset_dir, output_image_name)

            output_path=render_image(blender_file_path, base_image_path, effect_name)

            shutil.move(output_path, output_image_path)

            self.progress_dialog.hide()

    def set_image(self, pixmap):
        window_size = self.parent().size()  
        scaled_pixmap = pixmap.scaled(window_size * 0.5, Qt.AspectRatioMode.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setFixedSize(scaled_pixmap.size())


if __name__ == "__main__":

    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_blue.xml')
    window = MainWindow()
    window.setMinimumSize(1000, 800)
    window.show()
    sys.exit(app.exec())
