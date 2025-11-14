from insightface.app import FaceAnalysis

def main():
    app = FaceAnalysis(
        name="buffalo_s",                
        providers=["CPUExecutionProvider"] # forzamos CPU
    )

    # - ctx_id=0 -> CPU
    # - det_size=(320, 320) -> más pequeño, más rendimiento
    app.prepare(ctx_id=0, det_size=(320, 320))

    print("InsightFace cargado correctamente con buffalo_s")

if __name__ == "__main__":
    main()
