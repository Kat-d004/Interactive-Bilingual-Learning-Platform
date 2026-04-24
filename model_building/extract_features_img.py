'''
Created on 2017.12.9

@author: Richard
'''

import os
import librosa.display
import librosa.feature
import numpy as np
import matplotlib.pyplot as plt

number = 1

def extract_melSpectrogram(in_path, file, fmax, nMel, num):
    y, sr = librosa.load(in_path + file)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=nMel, fmax=fmax)
    
    # Create the output directory if it doesn't exist
    output_dir = '/home/kopano/Documents/School_Stuff/final_yr_project/Spoken_Number_Recognition-master/codes/spoken_numbers_wav/sesotho_spectrogram_image_ts/liphoofolo/' + str(num) + '/'
    os.makedirs(output_dir, exist_ok=True)
    
    plt.figure(figsize=(3, 3), dpi=100)
    librosa.display.specshow(librosa.power_to_db(S, ref=np.max), fmax=fmax)

    plt.xticks([])
    plt.yticks([])
    plt.tight_layout()
    
    # Save the image
    output_path = output_dir + file[:-3] + 'png'
    plt.savefig(output_path, bbox_inches='tight', pad_inches=-0.1)
    
    plt.close()   
    return

while(number<11):
    count = 0       # number of files processed

    in_path = '/home/kopano/Documents/School_Stuff/final_yr_project/mp3_data/sotho_collected/test/liphoofolo/'+ str(number) +'/'    #input directory
    for wavfile in os.listdir(in_path):
        
        # Input file
        extract_melSpectrogram(in_path, wavfile, 8000, 256, number)
        
        # Count processed files
        count += 1
        if count % 100 == 0:
            print ('%d files processed.' % count)

    print ('Done! processing files in %d' % number)
    number += 1
