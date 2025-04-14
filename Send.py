# 导入必要的库
#coding=utf-8
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score

# 加载鸢尾花数据集
iris = load_iris()
X = iris.data  # 特征数据
y = iris.target  # 真实标签

# 使用K-means进行聚类，设定聚类数为3（鸢尾花有3个种类）
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(X)

# 获取聚类结果
labels = kmeans.labels_

# 使用PCA进行降维，方便可视化
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X)

# 可视化聚类结果

mpl.rcParams['font.family'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False
plt.figure(figsize=(8, 6))
plt.scatter(X_2d[:, 0], X_2d[:, 1], c=labels, cmap='viridis', marker='o')
plt.title('鸢尾花数据集的K-means聚类结果')
plt.xlabel('PCA主成分 1')
plt.ylabel('PCA主成分 2')
plt.colorbar(label='聚类标签')
plt.show()

# 可视化真实标签
plt.figure(figsize=(8, 6))
plt.scatter(X_2d[:, 0], X_2d[:, 1], c=y, cmap='viridis', marker='o')
plt.title('鸢尾花数据集的真实标签')
plt.xlabel('PCA主成分 1')
plt.ylabel('PCA主成分 2')
plt.colorbar(label='真实标签')
plt.show()

# 计算聚类结果与真实标签之间的调整兰德指数（ARI）
ari = adjusted_rand_score(y, labels)
print(f"调整兰德指数（ARI）: {ari:.4f}")
