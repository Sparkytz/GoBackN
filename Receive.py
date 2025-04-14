import os
import cv2
import numpy as np
from skimage.feature import hog
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt

# 定义路径
data_dir = 'jaffedbase'  # 数据集路径

# 图像尺寸
IMG_SIZE = (64, 64)  # HOG特征提取需要一定的图像尺寸，通常使用64x64

# 表情标签与文件名的映射关系
emotion_map = {
    'anger': 'AN',
    'disgust': 'DI',
    'fear': 'FE',
    'happiness': 'HA',
    'neutral': 'NE',
    'sadness': 'SA',
    'surprise': 'SU'
}


# 读取所有图片并提取HOG特征
def extract_hog_features(data_dir):
    X = []  # 存储特征
    y = []  # 存储标签

    # 遍历数据集文件夹中的所有文件
    for img_name in os.listdir(data_dir):
        img_path = os.path.join(data_dir, img_name)

        # 读取图像并转为灰度图像
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        img = cv2.resize(img, IMG_SIZE)  # 调整图像尺寸

        # 提取HOG特征
        fd, hog_image = hog(img, pixels_per_cell=(8, 8), cells_per_block=(2, 2), visualize=True)
        X.append(fd)  # 将特征添加到X

        # 从文件名提取表情标签
        for emotion, code in emotion_map.items():
            if code in img_name:
                y.append(emotion)  # 将标签添加到y

    return np.array(X), np.array(y)


# 提取HOG特征和标签
X, y = extract_hog_features(data_dir)

# 标签编码
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# 切分数据集为训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

print(f"训练集大小: {X_train.shape[0]}, 测试集大小: {X_test.shape[0]}")
# 使用线性SVM进行训练
svm_model = SVC(kernel='linear', random_state=42)
svm_model.fit(X_train, y_train)

# 在测试集上进行预测
y_pred = svm_model.predict(X_test)

# 评估模型性能
print("分类报告:")
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

# 打印准确率
accuracy = accuracy_score(y_test, y_pred)
print(f"准确率: {accuracy * 100:.2f}%\n\n")
# 可视化HOG图像
def plot_hog_image(img, hog_image):
    plt.figure(figsize=(8, 4))
    plt.subplot(1, 2, 1)
    plt.imshow(img, cmap='gray')
    plt.title('原始图像')
    plt.subplot(1, 2, 2)
    plt.imshow(hog_image, cmap='gray')
    plt.title('HOG特征图像')
    plt.show()

# 随机选一张图像进行可视化
index = np.random.randint(0, len(X_train))
img_name = os.listdir(data_dir)[index]
img_path = os.path.join(data_dir, img_name)
img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
fd, hog_image = hog(img, pixels_per_cell=(8, 8), cells_per_block=(2, 2), visualize=True)

plot_hog_image(img, hog_image)
