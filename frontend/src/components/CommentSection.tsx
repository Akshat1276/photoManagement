import { useEffect, useState } from "react";
import {
	Avatar,
	Box,
	Button,
	CircularProgress,
	IconButton,
	List,
	ListItem,
	ListItemAvatar,
	ListItemText,
	TextField,
	Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import {
	BACKEND_URL,
	createPhotoCommentRequest,
	deletePhotoCommentRequest,
	fetchPhotoCommentsRequest,
	PhotoComment,
	updatePhotoCommentRequest,
} from "../api/client";
import { useAppSelector } from "../store/hooks";
import { useNotification } from "./NotificationProvider";

interface CommentSectionProps {
	photoId: number;
}

export function CommentSection({ photoId }: CommentSectionProps) {
	const user = useAppSelector((s) => s.auth.user);
	const notify = useNotification();

	const [comments, setComments] = useState<PhotoComment[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const [newComment, setNewComment] = useState("");
	const [submitting, setSubmitting] = useState(false);

	const [editingId, setEditingId] = useState<number | null>(null);
	const [editingContent, setEditingContent] = useState("");
	const [editingSaving, setEditingSaving] = useState(false);
	const [socketError, setSocketError] = useState<string | null>(null);

	useEffect(() => {
		const load = async () => {
			try {
				setLoading(true);
				setError(null);
				const data = await fetchPhotoCommentsRequest(photoId);
				setComments(data);
			} catch (err: any) {
				setError(err.response?.data?.detail || "Failed to load comments.");
			} finally {
				setLoading(false);
			}
		};

		load();
	}, [photoId]);

	// Realtime updates via WebSocket (Django Channels)
	useEffect(() => {
		if (!photoId) return;

		setSocketError(null);

		const wsScheme = BACKEND_URL.startsWith("https") ? "wss" : "ws";
		const base = BACKEND_URL.replace(/^http/, wsScheme).replace(/\/$/, "");
		const wsUrl = `${base}/ws/photos/${photoId}/comments/`;
		let closedByEffect = false;
		const socket = new WebSocket(wsUrl);

		socket.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				const action = data?.action as string | undefined;
				const comment = data?.comment as PhotoComment | { id: number } | undefined;
				if (!action || !comment) return;

				if (action === "created" || action === "updated") {
					const fullComment = comment as PhotoComment;
					setComments((prev) => {
						const exists = prev.some((c) => c.id === fullComment.id);
						if (exists && action === "created") {
							return prev;
						}
						if (exists && action === "updated") {
							return prev.map((c) => (c.id === fullComment.id ? fullComment : c));
						}
						// New comment: prepend to keep newest-first order
						return [fullComment, ...prev];
					});
				} else if (action === "deleted") {
					const id = (comment as { id: number }).id;
					if (typeof id === "number") {
						setComments((prev) => prev.filter((c) => c.id !== id));
					}
				}
			} catch (e) {
				// Ignore malformed messages
			}
		};

		socket.onerror = () => {
			if (!closedByEffect) {
				setSocketError("Live updates unavailable (websocket error).");
			}
		};

		return () => {
			closedByEffect = true;
			socket.close();
		};
	}, [photoId]);

	const canManageComment = (comment: PhotoComment) => {
		if (!user) return false;
		if (user.is_admin) return true;
		return comment.user_email === user.email;
	};

	const handleSubmit = async () => {
		if (!user) {
			notify("You must be logged in to comment.");
			return;
		}
		if (!newComment.trim()) return;

		try {
			setSubmitting(true);
			const created = await createPhotoCommentRequest(photoId, {
				content: newComment.trim(),
			});
			setComments((prev) => {
				const exists = prev.some((c) => c.id === created.id);
				if (exists) return prev;
				return [created, ...prev];
			});
			setNewComment("");
		} catch (err: any) {
			notify(err.response?.data?.detail || "Failed to post comment.");
		} finally {
			setSubmitting(false);
		}
	};

	const startEdit = (comment: PhotoComment) => {
		setEditingId(comment.id);
		setEditingContent(comment.content);
	};

	const cancelEdit = () => {
		setEditingId(null);
		setEditingContent("");
	};

	const saveEdit = async () => {
		if (!editingId || !editingContent.trim()) return;
		try {
			setEditingSaving(true);
			const updated = await updatePhotoCommentRequest(editingId, {
				content: editingContent.trim(),
			});
			setComments((prev) =>
				prev.map((c) => (c.id === updated.id ? updated : c))
			);
			cancelEdit();
		} catch (err: any) {
			notify(err.response?.data?.detail || "Failed to update comment.");
		} finally {
			setEditingSaving(false);
		}
	};

	const handleDelete = async (comment: PhotoComment) => {
		if (!window.confirm("Delete this comment?")) return;
		const id = comment.id;
		const prev = comments;
		setComments((c) => c.filter((x) => x.id !== id));
		try {
			await deletePhotoCommentRequest(id);
		} catch (err: any) {
			notify(err.response?.data?.detail || "Failed to delete comment.");
			setComments(prev);
		}
	};

	const renderCommentBody = (comment: PhotoComment) => {
		if (editingId === comment.id) {
			return (
				<Box display="flex" flexDirection="column" gap={1} mt={0.5}>
					<TextField
						size="small"
						multiline
						minRows={1}
						maxRows={4}
						value={editingContent}
						onChange={(e) => setEditingContent(e.target.value)}
					/>
					<Box display="flex" gap={1} justifyContent="flex-end">
						<Button
							size="small"
							onClick={cancelEdit}
							disabled={editingSaving}
						>
							Cancel
						</Button>
						<Button
							size="small"
							variant="contained"
							onClick={saveEdit}
							disabled={editingSaving}
						>
							Save
						</Button>
					</Box>
				</Box>
			);
		}

		return (
			<Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
				{comment.content}
			</Typography>
		);
	};

	return (
		<Box display="flex" flexDirection="column" height="100%">
			<Box
				sx={{
					flex: 1,
					overflowY: "auto",
					borderBottom: 1,
					borderColor: "divider",
					pr: 1,
				}}
			>
				{loading ? (
					<Box display="flex" justifyContent="center" mt={4}>
						<CircularProgress size={24} />
					</Box>
				) : error ? (
					<Typography color="error" mt={2}>
						{error}
					</Typography>
				) : socketError ? (
					<Typography color="warning.main" mt={1}>
						{socketError}
					</Typography>
				) : comments.length === 0 ? (
					<Box mt={2}>
						<Typography variant="body2" color="text.secondary">
							No comments yet. Be the first to comment.
						</Typography>
					</Box>
				) : (
					<List dense sx={{ py: 0 }}>
						{comments.map((comment) => {
							const initial = comment.user_email?.[0]?.toUpperCase() || "?";
							const createdAt = new Date(comment.created_at).toLocaleString();
							return (
								<ListItem
									key={comment.id}
									alignItems="flex-start"
									disableGutters
									secondaryAction={
										canManageComment(comment) && (
											<Box>
												<IconButton
													size="small"
													onClick={() => startEdit(comment)}
													aria-label="Edit comment"
												>
													<EditIcon fontSize="small" />
												</IconButton>
												<IconButton
													size="small"
													onClick={() => handleDelete(comment)}
													aria-label="Delete comment"
												>
													<DeleteIcon fontSize="small" />
												</IconButton>
											</Box>
										)
									}
									sx={{
										borderBottom: "1px solid",
										borderColor: "divider",
										px: 0,
									}}
								>
									<ListItemAvatar>
										<Avatar sx={{ width: 32, height: 32 }}>
											{initial}
										</Avatar>
									</ListItemAvatar>
									<ListItemText
										primary={
											<Box display="flex" alignItems="center" gap={1}>
												<Typography variant="subtitle2">
													{comment.user_email}
												</Typography>
												<Typography
													variant="caption"
													color="text.secondary"
												>
													{createdAt}
												</Typography>
											</Box>
										}
										secondary={renderCommentBody(comment)}
									/>
								</ListItem>
							);
						})}
					</List>
				)}
			</Box>

			<Box mt={1} display="flex" alignItems="flex-start" gap={1}>
				<TextField
					fullWidth
					size="small"
					variant="outlined"
					placeholder={
						user ? "Add a comment..." : "Log in to add a comment."
					}
					multiline
					minRows={1}
					maxRows={3}
					value={newComment}
					onChange={(e) => setNewComment(e.target.value)}
					disabled={!user || submitting}
					inputProps={{ "aria-label": "Add a comment" }}
				/>
				<Button
					variant="text"
					onClick={handleSubmit}
					disabled={!user || submitting || !newComment.trim()}
				>
					Post
				</Button>
			</Box>
		</Box>
	);
}