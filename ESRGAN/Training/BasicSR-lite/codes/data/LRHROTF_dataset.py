import os.path
import random
import numpy as np
import cv2
import torch
import torch.utils.data as data
import data.util as util

import sys
sys.path.append('/content/drive/MyDrive/ESRGAN/training/BasicSR-lite/codes/scripts')
sys.path.append('/content/drive/MyDrive/ESRGAN/training/BasicSR-lite/codes/data')
from augmentations import * #/augmentations

class LRHRDataset(data.Dataset):
    '''
    Read LR and HR image pairs.
    If only HR image is provided, generate LR image on-the-fly.
    The pair is ensured by 'sorted' function, so please check the name convention.
    '''

    def __init__(self, opt):
        super(LRHRDataset, self).__init__()
        self.opt = opt
        self.paths_LR = None
        self.paths_HR = None
        self.LR_env = None  # environment for lmdb
        self.HR_env = None
        self.output_sample_imgs = None

        # read image list from subset list txt
        if opt['subset_file'] is not None and opt['phase'] == 'train':
            with open(opt['subset_file']) as f:
                self.paths_HR = sorted([os.path.join(opt['dataroot_HR'], line.rstrip('\n')) \
                        for line in f])
            if opt['dataroot_LR'] is not None:
                raise NotImplementedError('Now subset only supports generating LR on-the-fly.')
        else:  # read image list from lmdb or image files
            # Check if dataroot_HR is a list of directories or a single directory. Note: lmdb will not currently work with a list
            HR_images_paths = opt['dataroot_HR']
            if type(HR_images_paths) is list:
                self.HR_env = []
                self.paths_HR = []
                for path in HR_images_paths:
                    HR_env, paths_HR = util.get_image_paths(opt['data_type'], path)
                    if type(HR_env) is list:
                        for imgs in HR_env:
                            self.HR_env.append(imgs)
                    for imgs in paths_HR:
                        self.paths_HR.append(imgs)
                if self.HR_env.count(None) == len(self.HR_env):
                    self.HR_env = None
                else:
                    self.HR_env = sorted(self.HR_env)
                self.paths_HR = sorted(self.paths_HR)
            elif type(HR_images_paths) is str:
                self.HR_env, self.paths_HR = util.get_image_paths(opt['data_type'], HR_images_paths)
            
            # Check if dataroot_LR is a list of directories or a single directory. Note: lmdb will not currently work with a list
            LR_images_paths = opt['dataroot_LR']
            if type(LR_images_paths) is list:
                self.LR_env = []
                self.paths_LR = []
                for path in LR_images_paths:
                    LR_env, paths_LR = util.get_image_paths(opt['data_type'], path)
                    if type(LR_env) is list:
                        for imgs in LR_env:
                            self.LR_env.append(imgs)
                    for imgs in paths_LR:
                        self.paths_LR.append(imgs)
                if self.LR_env.count(None) == len(self.LR_env):
                    self.LR_env = None
                else:
                    self.LR_env = sorted(self.LR_env)
                self.paths_LR = sorted(self.paths_LR)
            elif type(LR_images_paths) is str:
                self.LR_env, self.paths_LR = util.get_image_paths(opt['data_type'], LR_images_paths)

        assert self.paths_HR, 'Error: HR path is empty.'
        if self.paths_LR and self.paths_HR:
            # Modify to allow using HR and LR folders with different amount of images
            # - If an LR image pair is not found, downscale HR on the fly, else, use the LR
            # - If all LR are provided and 'lr_downscale' is enabled, randomize use of provided LR and OTF LR for augmentations
            """
            assert len(self.paths_LR) == len(self.paths_HR), \
                'HR and LR datasets have different number of images - {}, {}.'.format(\
                len(self.paths_LR), len(self.paths_HR))
            """
            #"""
            assert len(self.paths_HR) >= len(self.paths_LR), \
                'HR dataset contains less images than LR dataset  - {}, {}.'.format(\
                len(self.paths_LR), len(self.paths_HR))
            #"""
            if len(self.paths_LR) < len(self.paths_HR):
                print('LR contains less images than HR dataset  - {}, {}. Will generate missing images on the fly.'.format(len(self.paths_LR), len(self.paths_HR)))
                i=0
                tmp = []
                for idx in range(0, len(self.paths_HR)):
                    _, HRtail = os.path.split(self.paths_HR[idx])
                    if i < len(self.paths_LR):
                        LRhead, LRtail = os.path.split(self.paths_LR[i])
                        
                        if LRtail == HRtail:
                            LRimg_path = os.path.join(LRhead, LRtail)
                            tmp.append(LRimg_path)
                            i+=1
                        else:
                            LRimg_path = None
                            tmp.append(LRimg_path)
                    else: #if the last image is missing
                        LRimg_path = None
                        tmp.append(LRimg_path)
                self.paths_LR = tmp
        
        #self.random_scale_list = [1]

    def __getitem__(self, index):
        HR_path, LR_path = None, None
        scale = self.opt['scale']
        HR_size = self.opt['HR_size']
        LR_nc = self.opt['LR_nc']
        HR_nc = self.opt['HR_nc']
        if HR_size:
            LR_size = HR_size // scale
        
        ######## Read the images ########
        
        # Check if LR Path is provided
        if self.paths_LR:
            #If LR is provided, check if 'rand_flip_LR_HR' is enabled
            if self.opt['rand_flip_LR_HR'] and self.opt['phase'] == 'train':
                LRHRchance = random.uniform(0, 1)
                if self.opt['flip_chance']:
                    flip_chance = self.opt['flip_chance']
                else:
                    flip_chance = 0.05
                #print("Random Flip Enabled")
            # Normal case, no flipping:
            else:
                LRHRchance = 0.
                flip_chance = 0.
                #print("No Random Flip")

            # get HR and LR images
            # If enabled, random chance that LR and HR images are flipped
            # Normal case, no flipping
            # If img_LR (LR_path) doesn't exist, use img_HR (HR_path)
            if LRHRchance < (1- flip_chance):
                HR_path = self.paths_HR[index]
                LR_path = self.paths_LR[index]
                if LR_path is None:
                    LR_path = HR_path
                #print("HR kept")
            # Flipped case:
            # If img_HR (LR_path) doesn't exist, use img_HR (LR_path)
            else:
                HR_path = self.paths_LR[index]
                LR_path = self.paths_HR[index]
                if HR_path is None:
                    HR_path = LR_path
                #print("HR flipped")
            
            # Read the LR and HR images from the provided paths
            img_LR = util.read_img(self.LR_env, LR_path, LR_nc)
            img_HR = util.read_img(self.HR_env, HR_path, HR_nc)
            
            # Even if LR dataset is provided, force to generate aug_downscale % of downscales OTF from HR
            # The code will later make sure img_LR has the correct size
            if self.opt['aug_downscale']:
                aug_downscale = self.opt['aug_downscale']
                if np.random.rand() < aug_downscale:
                    img_LR = img_HR
            
        # If LR is not provided, use HR and modify on the fly
        else:
            HR_path = self.paths_HR[index]
            img_HR = util.read_img(self.HR_env, HR_path, HR_nc)
            img_LR = img_HR
        
        ######## Modify the images ########
        
        # HR modcrop in the validation / test phase
        if self.opt['phase'] != 'train':
            img_HR = util.modcrop(img_HR, scale)
        
        # change color space if necessary
        # Note: Changing the LR colorspace here could make it so some colors are introduced when 
        #  doing the augmentations later (ie: with Gaussian or Speckle noise), may be good if the
        #  model can learn to remove color noise in grayscale images, otherwise move to before
        #  converting to tensors
        # self.opt['color'] For both LR and HR as in the the original code, kept for compatibility
        # self.opt['color_HR'] and self.opt['color_LR'] for independent control
        if self.opt["color_HR"] or self.opt["color"]:  # Only change HR
            img_HR = util.channel_convert(img_HR.shape[2], self.opt["color_HR"] if self.opt["color_HR"] else self.opt["color"], [img_HR])[0]
        if self.opt["color_LR"] or self.opt["color"]:  # Only change LR
            img_LR = util.channel_convert(img_LR.shape[2], self.opt["color_LR"] if self.opt["color_LR"] else self.opt["color"], [img_LR])[0]
        
        ######## augmentations ########
        
        #augmentations during training
        if self.opt['phase'] == 'train':
            # HR downscale
            if self.opt['hr_downscale']: 
                ds_algo = 777
                if self.opt['hr_downscale_types']:
                    ds_algo = self.opt['hr_downscale_types']
                hr_downscale_amt = 2
                if self.opt['hr_downscale_amount']:
                    hr_downscale_amt = random.choice(self.opt['hr_downscale_amount'])
                # will ignore if 1 or if result is smaller than hr size
                if hr_downscale_amt > 1 and img_HR.shape[0]//hr_downscale_amt >= HR_size and img_HR.shape[1]//hr_downscale_amt >= HR_size:
                    img_HR, hr_scale_interpol_algo = scale_img(img_HR, hr_downscale_amt, algo=ds_algo)
                    np.clip(img_HR, 0., 1., out=img_HR)
                    # Downscales LR to match new size of HR if scale does not match after
                    if img_LR is not None and (img_HR.shape[0] // scale != img_LR.shape[0] or img_HR.shape[1] // scale != img_LR.shape[1]):
                        img_LR, lr_scale_interpol_algo = scale_img(img_LR, hr_downscale_amt, algo=ds_algo)
                        np.clip(img_LR, 0., 1., out=img_LR)

            # Validate there's an img_LR, if not, use img_HR
            if img_LR is None:
                img_LR = img_HR
                print("Image LR: ", LR_path, ("was not loaded correctly, using HR pair to downscale on the fly."))
            
            # Check that HR and LR have the same dimensions ratio, else, generate new LR from HR
            if img_HR.shape[0]//img_LR.shape[0] != img_HR.shape[1]//img_LR.shape[1]:
                print("Warning: img_LR dimensions ratio does not match img_HR dimensions ratio for: ", HR_path)
                img_LR = img_HR
            
            # Random Crop (reduce computing cost and adjust images to correct size first)
            if img_HR.shape[0] > HR_size or img_HR.shape[1] > HR_size:
                #Here the scale should be in respect to the images, not to the training scale (in case they are being scaled on the fly)
                scaleor = img_HR.shape[0]//img_LR.shape[0]
                img_HR, img_LR = random_crop_pairs(img_HR, img_LR, HR_size, scaleor) #augmentations/augmentationss
            
            # Or if the HR images are too small, Resize to the HR_size size and fit LR pair to LR_size too
            if img_HR.shape[0] < HR_size or img_HR.shape[1] < HR_size:
                print("Warning: Image: ", HR_path, " size does not match HR size: (", HR_size,"). The image size is: ", img_HR.shape)
                # rescale HR image to the HR_size 
                img_HR, _ = resize_img(np.copy(img_HR), (HR_size, HR_size), algo=cv2.INTER_LINEAR) #augmentations/augmentationss
                # rescale LR image to the LR_size (The original code discarded the img_LR and generated a new one on the fly from img_HR)
                img_LR, _ = resize_img(np.copy(img_LR), (LR_size, LR_size), algo=cv2.INTER_LINEAR) #augmentations/augmentationss
            
            # Randomly scale LR from HR during training if :
            # - LR dataset is not provided
            # - LR dataset is not in the correct scale
            # - Also to check if LR is not at the correct scale already (if img_LR was changed to img_HR)
            if img_LR.shape[0] != LR_size or img_LR.shape[1] != LR_size:
                ds_algo = 777 # default to matlab-like bicubic downscale
                if self.opt['lr_downscale']: # if manually set and scale algorithms are provided, then:
                    if self.opt['lr_downscale_types']:
                        ds_algo = self.opt['lr_downscale_types']
                else: # else, if for some reason img_LR is too large, default to matlab-like bicubic downscale
                    #if not self.opt['aug_downscale']: #only print the warning if not being forced to use HR images instead of LR dataset (which is a known case)
                    print("LR image is too large, auto generating new LR for: ", LR_path)
                img_LR, scale_interpol_algo = scale_img(img_LR, scale, algo=ds_algo)
                np.clip(img_LR, 0., 1., out=img_LR) # The generated LR sometimes get slightly out of the [0,1] range
            #"""
            
            # Rotations. 'use_flip' = 180 or 270 degrees (mirror), 'use_rot' = 90 degrees, 'HR_rrot' = random rotations +-45 degrees
            if (self.opt['use_flip'] or self.opt['use_rot']) and self.opt['hr_rrot']:
                if np.random.rand() > 0.5:
                    img_LR, img_HR = util.augment([img_LR, img_HR], self.opt['use_flip'], \
                        self.opt['use_rot'])
                else:
                    if np.random.rand() > 0.5: # randomize the random rotations, so half the images are the original
                        img_HR, img_LR = random_rotate_pairs(img_HR, img_LR, HR_size, scale)
            elif (self.opt['use_flip'] or self.opt['use_rot']) and not self.opt['hr_rrot']:
                # augmentations - flip, rotate
                img_LR, img_HR = util.augment([img_LR, img_HR], self.opt['use_flip'], \
                    self.opt['use_rot'])
            elif self.opt['hr_rrot']:
                if np.random.rand() > 0.5: # randomize the random rotations, so half the images are the original
                    img_HR, img_LR = random_rotate_pairs(img_HR, img_LR, HR_size, scale) #augmentations/augmentationss
            
            
            # Final checks
            # if the resulting HR image size so far is too large or too small, resize HR to the correct size and downscale to generate a new LR on the fly
            if img_HR.shape[0] != HR_size or img_HR.shape[1] != HR_size:
                print("Image: ", HR_path, " size does not match HR size: (", HR_size,"). The image size is: ", img_HR.shape)
                # rescale HR image to the HR_size 
                img_HR, _ = resize_img(np.copy(img_HR), (HR_size, HR_size), algo=cv2.INTER_LINEAR) #augmentations/augmentationss
                if self.opt['lr_downscale_types']: # if manually provided and scale algorithms are provided, then:
                    ds_algo = self.opt['lr_downscale_types']
                else:
                    ## using matlab imresize to generate LR pair
                    ds_algo = 777
                img_LR, _ = scale_img(img_HR, scale, algo=ds_algo) #augmentations/augmentationss
            # if the resulting LR so far does not have the correct dimensions, also generate a new HR-LR image pair on the fly
            if img_LR.shape[0] != LR_size or img_LR.shape[0] != LR_size:
                print("Image: ", LR_path, " size does not match LR size: (", HR_size//scale,"). The image size is: ", img_LR.shape)
                # rescale HR image to the HR_size (should not be needed, but something went wrong before, just for sanity)
                img_HR, _ = resize_img(np.copy(img_HR), (HR_size, HR_size), algo=cv2.INTER_LINEAR) #augmentations/augmentationss
                if self.opt['lr_downscale_types']: # if manually provided and scale algorithms are provided, then:
                    ds_algo = self.opt['lr_downscale_types']
                else:
                    ## using matlab imresize to generate LR pair
                    ds_algo = 777
                img_LR, _ = scale_img(img_HR, scale, algo=ds_algo) #augmentations/augmentationss
            
            
            # Below are the LR On The Fly augmentations
            # Add noise to HR if enabled AND noise types are provided (for noise2noise and similar)
            if self.opt['hr_noise']:
                if self.opt['hr_noise_types']:
                    img_HR, hr_noise_algo = noise_img(img_HR, noise_types=self.opt['hr_noise_types']) #augmentations/augmentationss
                else:
                    print("Noise types 'hr_noise_types' not defined. Skipping OTF noise for HR.")
            
            # Create color fringes
            # Caution: Can easily destabilize a model
            # Only applied to a small % of the images. Around 20% and 50% appears to be stable.
            if self.opt['lr_fringes']:
                lr_fringes_chance = self.opt['lr_fringes_chance'] if self.opt['lr_fringes_chance'] else 0.4
                if np.random.rand() > (1.- lr_fringes_chance):
                    img_LR = translate_chan(img_LR)
            
            #"""
            #v LR blur AND blur types are provided, else will skip
            if self.opt['lr_blur']:
                if self.opt['lr_blur_types']:
                    img_LR, blur_algo, blur_kernel_size = blur_img(img_LR, blur_algos=self.opt['lr_blur_types'])
                else:
                    print("Blur types 'lr_blur_types' not defined. Skipping OTF blur.")
            #"""
                
            #"""
            #v LR primary noise: Add noise to LR if enabled AND noise types are provided, else will skip
            if self.opt['lr_noise']:
                if self.opt['lr_noise_types']:
                    img_LR, noise_algo = noise_img(img_LR, noise_types=self.opt['lr_noise_types'])
                else:
                    print("Noise types 'lr_noise_types' not defined. Skipping OTF noise.")
            #v LR secondary noise: Add additional noise to LR if enabled AND noise types are provided, else will skip
            if self.opt['lr_noise2']:
                if self.opt['lr_noise_types2']:
                    img_LR, noise_algo2 = noise_img(img_LR, noise_types=self.opt['lr_noise_types2'])
                else:
                    print("Noise types 'lr_noise_types2' not defined. Skipping OTF secondary noise.")
            #"""
                
            #"""
            #v LR cutout / LR random erasing (for inpainting/classification tests)
            if self.opt['lr_cutout'] and (self.opt['lr_erasing']  != True):
                img_LR = cutout(img_LR, img_LR.shape[0] // 2)
            elif self.opt['lr_erasing'] and (self.opt['lr_cutout']  != True): 
                img_LR = random_erasing(img_LR)
            elif self.opt['lr_cutout'] and self.opt['lr_erasing']: 
                if np.random.rand() > 0.5: #only do cutout or erasing, not both at the same time
                    img_LR = cutout(img_LR, img_LR.shape[0] // 2, p=0.5)
                else:
                    img_LR = random_erasing(img_LR, p=0.5, modes=[3])                
            #"""
            
            # Apply "auto levels" to images
            rand_levels = (1 - self.opt['rand_auto_levels']) if self.opt['rand_auto_levels'] else 1 # Randomize for augmentations
            if self.opt['auto_levels'] and np.random.rand() > rand_levels:
                if self.opt['auto_levels'] == 'HR':
                    img_HR = simplest_cb(img_HR)
                elif self.opt['auto_levels'] == 'LR':
                    img_LR = simplest_cb(img_LR)
                elif self.opt['auto_levels'] == True or self.opt['auto_levels'] == 'Both':
                    img_HR = simplest_cb(img_HR)
                    img_LR = simplest_cb(img_LR)
            
            # Apply unsharpening mask to HR images
            rand_unsharp = (1 - self.opt['hr_rand_unsharp']) if self.opt['hr_rand_unsharp'] else 1 # Randomize for augmentations
            if self.opt['hr_unsharp_mask'] and np.random.rand() > rand_unsharp:
                img_HR = unsharp_mask(img_HR)
            
            # Apply unsharpening mask to LR images
            rand_unsharp = (1 - self.opt["lr_rand_unsharp"]) if self.opt["lr_rand_unsharp"] else 1 # Randomize for augmentations
            if self.opt["lr_unsharp_mask"] and np.random.rand() > rand_unsharp:
                img_LR = unsharp_mask(img_LR)
        
        # For testing and validation
        if self.opt['phase'] != 'train':
            # Randomly downscale LR if enabled 
            if self.opt['lr_downscale']:
                if self.opt['lr_downscale_types']:
                    img_LR, scale_interpol_algo = scale_img(img_LR, scale, algo=self.opt['lr_downscale_types'])
                else: # Default to matlab-like bicubic downscale
                    img_LR, scale_interpol_algo = scale_img(img_LR, scale, algo=777)
        
        # Alternative position for changing the colorspace of LR. 
        # if self.opt['color_LR']: # Only change LR
            # img_LR = util.channel_convert(img_LR.shape[2], self.opt['color'], [img_LR])[0]
            
        # Debug
        # Save img_LR and img_HR images to a directory to visualize what is the result of the on the fly augmentations
        # DO NOT LEAVE ON DURING REAL TRAINING
        # self.output_sample_imgs = True
        if self.opt['phase'] == 'train':
            if self.output_sample_imgs:
                import os
                # LR_dir, im_name = os.path.split(LR_path)
                HR_dir, im_name = os.path.split(HR_path)
                #baseHRdir, _ = os.path.split(HR_dir)
                #debugpath = os.path.join(baseHRdir, os.sep, 'sampleOTFimgs')
                
                # debugpath = os.path.join(os.path.split(LR_dir)[0], 'sampleOTFimgs')
                debugpath = os.path.join('D:/tmp_test', 'sampleOTFimgs')
                #print(debugpath)
                if not os.path.exists(debugpath):
                    os.makedirs(debugpath)
                
                import uuid
                hex = uuid.uuid4().hex
                cv2.imwrite(debugpath+"\\"+im_name+hex+'_LR.png',img_LR*255) #random name to save + had to multiply by 255, else getting all black image
                cv2.imwrite(debugpath+"\\"+im_name+hex+'_HR.png',img_HR*255) #random name to save + had to multiply by 255, else getting all black image
            
        ######## Convert images to PyTorch Tensors ########
        
        """
        if (img_HR.min() < -1):
            print("HR.min :", img_HR.min())
            print(HR_path)
        if (img_HR.max() > 1):
            print("HR.max :", img_HR.max())
            print(HR_path)
        if (img_LR.min() < -1):
            print("LR.min :", img_LR.min())
            print(LR_path)
        if (img_LR.max() > 1):
            print("LR.max :", img_LR.max())
            print(LR_path)
        #"""
        
        # BGR to RGB, HWC to CHW, numpy to tensor
        if img_HR.shape[2] == 3:
            img_HR = img_HR[:, :, [2, 1, 0]]
            img_LR = img_LR[:, :, [2, 1, 0]]        
        # BGRA to RGBA, HWC to CHW, numpy to tensor
        elif img_LR.shape[2] == 4:
            img_HR = img_HR[:, :, [2, 1, 0, 3]]
            img_LR = img_LR[:, :, [2, 1, 0, 3]]

        img_HR = torch.from_numpy(np.ascontiguousarray(np.transpose(img_HR, (2, 0, 1)))).float()
        img_LR = torch.from_numpy(np.ascontiguousarray(np.transpose(img_LR, (2, 0, 1)))).float()
        
        if LR_path is None:
            LR_path = HR_path
        return {'LR': img_LR, 'HR': img_HR, 'LR_path': LR_path, 'HR_path': HR_path} 

    def __len__(self):
        return len(self.paths_HR)
        
