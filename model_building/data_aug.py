import librosa
import librosa.display
import numpy as np
import soundfile as sf
import os
import itertools
import warnings
warnings.filterwarnings('ignore')

class CombinatorialAudioAugmentor:
    """
    Audio data augmentor that creates ALL valid combinations of augmentations.
    Applies combinatorial logic: from each augmentation type (time, pitch, gain, noise),
    you can choose at most one variation (or none).
    """
    
    def __init__(self, sr=44100):
        """
        Initialize the augmentor with sampling rate.
        
        Args:
            sr (int): Sampling rate (default: 44100)
        """
        self.sr = sr
        
        # Default augmentation parameters - EASILY CONFIGURABLE
        self.aug_params = {
            'time': {
                'lower': 0.85,   # Slower speed
                'higher': 1.15   # Faster speed
            },
            'pitch': {
                'lower': -2.0,   # Lower pitch
                'higher': 2.0    # Higher pitch
            },
            'gain': {
                'lower': 0.5,    # Quieter
                'higher': 2.0    # Louder
            },
            'noise': {
                'lower': 0.1,    # Less noise
                'higher': 0.3    # More noise
            }
        }
        
        # Track all possible combinations
        self.all_combinations = []
    
    def configure_parameters(self, **kwargs):
        """
        Configure augmentation parameters easily.
        """
        for key, value in kwargs.items():
            if 'time' in key:
                if 'lower' in key:
                    self.aug_params['time']['lower'] = value
                elif 'higher' in key:
                    self.aug_params['time']['higher'] = value
            elif 'pitch' in key:
                if 'lower' in key:
                    self.aug_params['pitch']['lower'] = value
                elif 'higher' in key:
                    self.aug_params['pitch']['higher'] = value
            elif 'gain' in key:
                if 'lower' in key:
                    self.aug_params['gain']['lower'] = value
                elif 'higher' in key:
                    self.aug_params['gain']['higher'] = value
            elif 'noise' in key:
                if 'lower' in key:
                    self.aug_params['noise']['lower'] = value
                elif 'higher' in key:
                    self.aug_params['noise']['higher'] = value
    
    def time_stretch(self, audio, factor):
        """Apply time stretching while preserving pitch."""
        stretched_audio = librosa.effects.time_stretch(audio, rate=factor)
        
        if len(stretched_audio) != len(audio):
            stretched_audio = librosa.resample(stretched_audio, 
                                             orig_sr=self.sr, 
                                             target_sr=self.sr)
            if len(stretched_audio) > len(audio):
                stretched_audio = stretched_audio[:len(audio)]
            else:
                stretched_audio = np.pad(stretched_audio, 
                                       (0, len(audio) - len(stretched_audio)), 
                                       mode='constant')
        
        return stretched_audio
    
    def pitch_shift(self, audio, semitones):
        """Apply pitch shifting while preserving duration."""
        if semitones == 0:
            return audio.copy()
        
        shifted_audio = librosa.effects.pitch_shift(audio, 
                                                   sr=self.sr, 
                                                   n_steps=semitones)
        return shifted_audio
    
    def add_noise(self, audio, noise_scale):
        """Add Gaussian (white) noise to audio."""
        noise = np.random.normal(0, 1, len(audio))
        audio_variance = np.var(audio) if np.var(audio) > 0 else 1
        noise = noise * np.sqrt(audio_variance) * noise_scale
        
        noisy_audio = audio + noise
        
        max_val = np.max(np.abs(noisy_audio))
        if max_val > 1.0:
            noisy_audio = noisy_audio / max_val
            
        return noisy_audio
    
    def adjust_gain(self, audio, gain_factor):
        """Adjust the gain (amplitude) of the audio."""
        gained_audio = audio * gain_factor
        
        max_val = np.max(np.abs(gained_audio))
        if max_val > 1.0:
            gained_audio = gained_audio / max_val
            
        return gained_audio
    
    def generate_all_combinations(self):
        """
        Generate all valid combinations of augmentations.
        For each augmentation type (time, pitch, gain, noise),
        we can choose: none, lower, or higher.
        """
        # Create choice sets for each augmentation type
        time_choices = ['none', 'lower', 'higher']
        pitch_choices = ['none', 'lower', 'higher']
        gain_choices = ['none', 'lower', 'higher']
        noise_choices = ['none', 'lower', 'higher']
        
        # Generate all combinations (Cartesian product)
        all_combos = list(itertools.product(
            time_choices, pitch_choices, gain_choices, noise_choices
        ))
        
        # Remove the "all none" combination (we'll handle original separately)
        valid_combos = [combo for combo in all_combos if combo != ('none', 'none', 'none', 'none')]
        
        self.all_combinations = valid_combos
        return valid_combos
    
    def apply_combination(self, audio, combination):
        """
        Apply a specific combination of augmentations to audio.
        
        Args:
            audio (numpy.ndarray): Original audio
            combination (tuple): (time_choice, pitch_choice, gain_choice, noise_choice)
            
        Returns:
            numpy.ndarray: Augmented audio
            str: Description of the combination
        """
        augmented = audio.copy()
        description_parts = []
        
        time_choice, pitch_choice, gain_choice, noise_choice = combination
        
        # Apply time stretching if chosen
        if time_choice != 'none':
            factor = self.aug_params['time'][time_choice]
            augmented = self.time_stretch(augmented, factor)
            description_parts.append(f"time_{time_choice}_{factor:.2f}")
        
        # Apply pitch shift if chosen
        if pitch_choice != 'none':
            semitones = self.aug_params['pitch'][pitch_choice]
            augmented = self.pitch_shift(augmented, semitones)
            description_parts.append(f"pitch_{pitch_choice}_{abs(semitones):.1f}")
        
        # Apply gain adjustment if chosen
        if gain_choice != 'none':
            gain_factor = self.aug_params['gain'][gain_choice]
            augmented = self.adjust_gain(augmented, gain_factor)
            description_parts.append(f"gain_{gain_choice}_{gain_factor:.1f}")
        
        # Apply noise addition if chosen
        if noise_choice != 'none':
            noise_scale = self.aug_params['noise'][noise_choice]
            augmented = self.add_noise(augmented, noise_scale)
            description_parts.append(f"noise_{noise_choice}_{noise_scale:.2f}")
        
        # Create descriptive string
        if description_parts:
            description = "_".join(description_parts)
        else:
            description = "original"
        
        return augmented, description
    
    def augment_single_file(self, audio_path, output_dir):
        """
        Apply ALL valid combinations of augmentations to a single audio file.
        
        Args:
            audio_path (str): Path to input audio file
            output_dir (str): Directory to save augmented files
            
        Returns:
            dict: Dictionary of all created files
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Load audio file
        audio, sr = librosa.load(audio_path, sr=self.sr)
        
        # Get base filename
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        
        # Save original
        original_path = os.path.join(output_dir, f"{base_name}_original.wav")
        sf.write(original_path, audio, sr)
        
        # Generate all valid combinations
        combinations = self.generate_all_combinations()
        
        results = {
            'original': original_path,
            'augmented': []
        }
        
        print(f"\nAugmenting: {base_name}")
        print("-" * 40)
        print(f"Total combinations to create: {len(combinations)}")
        print("-" * 40)
        
        # Apply each combination
        for i, combination in enumerate(combinations, 1):
            # Apply the combination
            augmented_audio, description = self.apply_combination(audio, combination)
            
            # Create filename
            filename = f"{base_name}_{description}.wav"
            output_path = os.path.join(output_dir, filename)
            
            # Save the file
            sf.write(output_path, augmented_audio, sr)
            
            # Store results
            results['augmented'].append({
                'path': output_path,
                'combination': combination,
                'description': description
            })
            
            print(f"Created {i:3d}/{len(combinations)}: {filename}")
        
        return results
    
    def augment_folder(self, input_folder, output_base_dir):
        """
        Apply combinatorial augmentation to all audio files in a folder.
        
        Args:
            input_folder (str): Path to folder containing audio files
            output_base_dir (str): Base directory to save augmented files
            
        Returns:
            dict: Dictionary mapping original files to their augmented versions
        """
        all_results = {}
        
        # Get all audio files in the folder
        audio_extensions = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
        audio_files = []
        
        for file in os.listdir(input_folder):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(os.path.join(input_folder, file))
        
        if not audio_files:
            print(f"No audio files found in {input_folder}")
            return all_results
        
        print(f"Found {len(audio_files)} audio file(s) in {input_folder}")
        
        for audio_file in audio_files:
            # Create subdirectory for each original file
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            file_output_dir = output_base_dir #os.path.join(output_base_dir , base_name)
            
            # Augment the file
            print(f"\n{'='*60}")
            print(f"Processing: {base_name}")
            print(f"Saving to: {file_output_dir}")
            print('='*60)
            
            results = self.augment_single_file(audio_file, file_output_dir)
            all_results[audio_file] = results
            
        return all_results
    
    def generate_summary_report(self, augmentation_results):
        """
        Generate a summary report of all created augmentations.
        """
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("COMBINATORIAL AUGMENTATION SUMMARY REPORT")
        report_lines.append("=" * 80)
        
        report_lines.append("\nCONFIGURED PARAMETERS:")
        report_lines.append("-" * 40)
        for aug_type, params in self.aug_params.items():
            report_lines.append(f"{aug_type.title()}:")
            for param_type, value in params.items():
                if aug_type == 'pitch':
                    report_lines.append(f"  • {param_type}: {value:+.1f} semitones")
                elif aug_type == 'gain':
                    report_lines.append(f"  • {param_type}: ×{value:.1f}")
                elif aug_type == 'noise':
                    report_lines.append(f"  • {param_type}: {value:.2f}")
                else:
                    report_lines.append(f"  • {param_type}: {value:.2f}x")
        
        # Calculate expected number of combinations
        # For 4 augmentation types, each with 3 choices (none, lower, higher)
        # Total combinations: 3^4 = 81
        # Minus the "all none" combination = 80 augmented files per original
        expected_per_file = 3 ** 4 - 1  # 80 combinations
        
        report_lines.append(f"\nEXPECTED COMBINATIONS PER FILE: {expected_per_file}")
        report_lines.append("(Time: none/lower/higher × Pitch: none/lower/higher × ")
        report_lines.append(" Gain: none/lower/higher × Noise: none/lower/higher)")
        report_lines.append(f"Total possibilities: 3^4 = 81, minus original = {expected_per_file}")
        
        total_files_created = 0
        
        for audio_file, results in augmentation_results.items():
            base_name = os.path.basename(audio_file)
            report_lines.append(f"\nFile: {base_name}")
            report_lines.append(f"Original: {results['original']}")
            
            augmented_count = len(results['augmented'])
            total_per_file = 1 + augmented_count  # Original + augmented
            total_files_created += total_per_file
            
            report_lines.append(f"Augmented files created: {augmented_count}")
            report_lines.append(f"Total for this file: {total_per_file} files")
            
            # Show breakdown by number of augmentations applied
            breakdown = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            for aug in results['augmented']:
                # Count non-'none' choices in the combination
                num_augmentations = sum(1 for choice in aug['combination'] if choice != 'none')
                breakdown[num_augmentations] += 1
            
            report_lines.append("Breakdown by number of augmentations applied:")
            for num_augs, count in breakdown.items():
                if num_augs > 0:  # Skip 0 (original)
                    report_lines.append(f"  • {num_augs} augmentation(s): {count} files")
        
        report_lines.append("\n" + "=" * 80)
        report_lines.append(f"GRAND TOTAL: {total_files_created} files created")
        report_lines.append(f"({len(augmentation_results)} originals + {total_files_created - len(augmentation_results)} augmented)")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


def main():
    """
    Main function to demonstrate combinatorial augmentation.
    """
    # Initialize augmentor
    augmentor = CombinatorialAudioAugmentor(sr=48000)
    
    # Configure your desired parameters
    augmentor.configure_parameters(
        time_lower=0.8,      # 20% slower
        time_higher=1.2,     # 20% faster
        pitch_lower=-1.5,    # 1.5 semitones lower
        pitch_higher=1.5,    # 1.5 semitones higher
        gain_lower=0.7,      # 70% volume
        gain_higher=1.5,     # 150% volume
        noise_lower=0.05,    # Very little noise
        noise_higher=0.25    # Moderate noise
    )
    
    # Input folder containing all your audio files
    input_folder = "/home/kopano/Documents/School_Stuff/final_yr_project/mp3_data/sotho_collected/combined_raw_data/animals/10"
    
    # Output base directory for augmented files
    output_base_dir = "/home/kopano/Documents/School_Stuff/final_yr_project/mp3_data/aug_data/collected/liphoofolo/10"
    
    # Apply combinatorial augmentation to all files in the folder
    results = augmentor.augment_folder(input_folder, output_base_dir)
    
    # Generate and print summary report
    '''if results:
        report = augmentor.generate_summary_report(results)
        print(report)
        
        # Save report to file
        report_file = os.path.join(output_base_dir, "combinatorial_augmentation_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\nDetailed report saved to: {report_file}")
    else:
        print("No files were processed.")'''


if __name__ == "__main__":
    main()