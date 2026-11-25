import os
import subprocess

# --- CONFIGURACIÓ DE RUTES ---
ELASTIX_PATH = "/Volumes/COPIA/TFM/REGISTRA-MNI/elastix-5.0.0-mac/elastix"
TRANSFORMIX_PATH = "/Volumes/COPIA/TFM/REGISTRA-MNI/elastix-5.0.0-mac/transformix"
LIB_PATH = "/Volumes/COPIA/TFM/REGISTRA-MNI/elastix-5.0.0-mac/lib"

ATLAS_MNI = "/Volumes/COPIA/TFM/REGISTRA-MNI/MorelAtlasMNI152/MNI152_T1_1mm.nii.gz"
PARAM_AFFINE = "/Volumes/COPIA/TFM/REGISTRA-MNI/Parameters/Par0010affine.txt"
PARAM_BSPLINE = "/Volumes/COPIA/TFM/REGISTRA-MNI/Parameters/Par0010bspline.txt"

INPUT_DIR = "/Volumes/COPIA/TFM/DATA SET/TEST SET MODALITATS/DWI/N4_CORRECTED"
OUTPUT_BASE = "/Volumes/COPIA/TFM/DATA SET/REGISTRADES"

# Configuració de l'entorn per a les llibreries d'Elastix en Mac
env = os.environ.copy()
env["DYLD_LIBRARY_PATH"] = LIB_PATH

os.makedirs(OUTPUT_BASE, exist_ok=True)

def run_registration_batch():
    # Busquem fitxers corregits amb N4 (evitant fitxers ocults de Mac)
    files = sorted([f for f in os.listdir(INPUT_DIR) 
                   if f.endswith('_N4.nii.gz') and not f.startswith('._')])
    
    print(f"S'han trobat {len(files)} fitxers per registrar.")

    for i, file_name in enumerate(files):
        moving_image = os.path.join(INPUT_DIR, file_name)
        subject_id = file_name.replace('_N4.nii.gz', '')
        subject_out = os.path.join(OUTPUT_BASE, subject_id)
        os.makedirs(subject_out, exist_ok=True)

        print(f"[{i+1}/{len(files)}] Registrant al MNI: {subject_id}...")

        # 1. ELASTIX: Calcula Affine + B-Spline
        # El pas 0 és Affine, el pas 1 és B-Spline
        cmd_elastix = [
            ELASTIX_PATH,
            "-f", ATLAS_MNI,
            "-m", moving_image,
            "-out", subject_out,
            "-p", PARAM_AFFINE,
            "-p", PARAM_BSPLINE
        ]
        
        subprocess.run(cmd_elastix, env=env, stdout=subprocess.DEVNULL)

        # 2. TRANSFORMIX: Apliquem la transformació final combinada
        # El fitxer .1.txt conté tota la informació de registre acumulada
        tp_final = os.path.join(subject_out, "TransformParameters.1.txt")
        
        if os.path.exists(tp_final):
            print(f"  > Aplicant transformació final (Resampling)...")
            cmd_transformix = [
                TRANSFORMIX_PATH,
                "-in", moving_image,
                "-out", subject_out,
                "-tp", tp_final
            ]
            subprocess.run(cmd_transformix, env=env, stdout=subprocess.DEVNULL)
            
            # Renomenar el resultat final per a la teva base de dades
            res_old = os.path.join(subject_out, "result.nii.gz")
            res_new = os.path.join(subject_out, f"{subject_id}_MNI_FINAL.nii.gz")
            
            if os.path.exists(res_old):
                if os.path.exists(res_new): os.remove(res_new)
                os.rename(res_old, res_new)
                print(f"  ✅ FET: {os.path.basename(res_new)}")
        else:
            print(f"  ❌ Error: No s'ha pogut generar la transformació per a {subject_id}")

if __name__ == "__main__":
    run_registration_batch()