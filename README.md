# Projet S9 : Super Resolution

#### Dependencies
- Python 3
- [PyTorch >= 1.0](https://pytorch.org/) (CUDA version >= 7.5 if installing with CUDA. [More details](https://pytorch.org/get-started/previous-versions/))
- Python packages:  `pip install numpy opencv-python`

### Test models
1. Clone this github repo.
```
git clone https://github.com/xinntao/ESRGAN
```
2. Place your own **low-resolution images** in `./LR` folder.
3. Download pretrained models from [Google Drive](https://drive.google.com/drive/u/0/folders/17VYV_SoZZesU6mbxz2dMAIccSSlqLecY) and place them in `./models`.
4. Run test.py file :
```
python test.py
```
5. The results are in `./results` folder.
