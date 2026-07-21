# Stage 2 of the recommendation flow (per the .md spec):
#   GNN candidate generation -> context-aware ranking -> this module's output
#
# This module should NOT talk to Spotify or the graph builder directly --
# it takes already-built inputs (candidate tracks + their GNN embeddings +
# the current context vector) and returns a ranked list. Keeps it testable
# without a live Spotify session or a trained model.
#
# TODO: score_candidates(candidate_track_ids, track_embeddings, context_vector,
#                         user_embedding=None) -> list[tuple[str, float]]
#   Concatenates [track_embedding, context_embedding, user_embedding] per the
#   .md spec's ranking MLP shape and runs it through the trained ranker.
#   Returns (track_id, score) pairs sorted descending.
#
# TODO: get_next_recommendations(playlist_track_ids, context_vector,
#                                 exclude_track_ids, limit=3) -> list[str]
#   The function playback_loop.py actually calls each poll: given the
#   current playlist's candidate pool and context, exclude tracks already
#   queued/recently played (exclude_track_ids), and return the top `limit`
#   track ids to hand to app/spotify/queue.py.
#
# TODO: decide fallback behavior when no trained GNN/ranker model is loaded
#   yet -- e.g. fall back to the popularity baseline from the .md spec so
#   playback_loop.py has something to call before training is done.
