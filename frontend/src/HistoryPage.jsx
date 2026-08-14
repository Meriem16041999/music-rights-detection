function HistoryPage({
  projects,
  onOpen,
  onDelete,
  onBack,
  title = "Historique",
}) {
  return (
    <div className="history-page">
      <div className="history-topbar">
        <div>
          <h1>{title}</h1>
          <p>
            Ouvre un projet enregistré pour reprendre les
            modifications.
          </p>
        </div>

        <button
          className="history-back-button"
          onClick={onBack}
        >
          ← Retour au projet
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="history-empty">
          <h2>Aucun projet enregistré</h2>
          <p>
            Sauvegarde une émission pour la retrouver ici.
          </p>
        </div>
      ) : (
        <div className="history-grid">
          {projects.map((project) => {
            const quality =
              Number(project.quality_score || 0);

            return (
              <article
                className="history-card"
                key={project.id}
              >
                <div className="history-card-header">
                  <div>
                    <span className="history-mode">
                      {project.mode === "classic"
                        ? "Émission classique"
                        : "Mot de Passe / MDP"}
                    </span>

                    <h2>{project.name}</h2>

                    <p className="history-video">
                      {project.video_name ||
                        "Vidéo non renseignée"}
                    </p>
                  </div>

                  <div
                    className={`quality-circle ${
                      quality >= 90
                        ? "quality-circle-good"
                        : quality >= 60
                          ? "quality-circle-warning"
                          : "quality-circle-bad"
                    }`}
                  >
                    {quality}%
                  </div>
                </div>

                <div className="history-stats">
                  <div className="history-stat">
                    <strong>
                      {project.segment_count || 0}
                    </strong>
                    <span>segments</span>
                  </div>

                  <div className="history-stat">
                    <strong>
                      {project.validated_count || 0}
                    </strong>
                    <span>validés</span>
                  </div>

                  <div className="history-stat">
                    <strong>
                      {project.review_count || 0}
                    </strong>
                    <span>à vérifier</span>
                  </div>

                  <div className="history-stat">
                    <strong>
                      {project.missing_count || 0}
                    </strong>
                    <span>non validés</span>
                  </div>
                </div>

                <div className="history-card-footer">
                  <small>
                    Modifié le{" "}
                    {project.updated_at
                      ? new Date(
                          project.updated_at
                        ).toLocaleString("fr-FR")
                      : "—"}
                  </small>

                  <div className="history-actions">
                    <button
                      className="history-open-button"
                      onClick={() =>
                        onOpen(project.id)
                      }
                    >
                      Ouvrir
                    </button>

                    <button
                      className="history-delete-button"
                      onClick={() =>
                        onDelete(project.id)
                      }
                    >
                      Supprimer
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default HistoryPage;