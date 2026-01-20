import { useEffect, useState } from "react";
import { useNotification } from "../components/NotificationProvider";
import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import {
  createEventRequest,
  deleteEventRequest,
  fetchEventsRequest,
  fetchEventPhotosRequest,
  downloadMultiplePhotos,
} from "../api/client";
import type { Event } from "../api/client";
import { useAppSelector } from "../store/hooks";

/* ---------- Utility ---------- */
function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/* ---------- Component ---------- */
export function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [eventCovers, setEventCovers] = useState<Record<number, string | null>>(
    {}
  );
  const [selectedEvents, setSelectedEvents] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const user = useAppSelector((s) => s.auth.user);
  const navigate = useNavigate();
  const notify = useNotification();

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchEventsRequest(); // non-paginated
        setEvents(data);

        const covers: Record<number, string | null> = {};
        await Promise.all(
          data.map(async (event) => {
            try {
              const photos = await fetchEventPhotosRequest(event.slug);
              covers[event.id] =
                photos[0]?.image_thumbnail ||
                photos[0]?.image_watermarked ||
                photos[0]?.image_original ||
                null;
            } catch {
              covers[event.id] = null;
            }
          })
        );
        setEventCovers(covers);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load events.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);
  const toggleEventSelection = (eventId: number) => {
    setSelectedEvents((prev) =>
      prev.includes(eventId)
        ? prev.filter((id) => id !== eventId)
        : [...prev, eventId]
    );
  };

  const handleBulkDownload = async (
    variant: "watermarked" | "original"
  ) => {
    if (!selectedEvents.length) {
      notify("No events selected");
      return;
    }

    setDownloading(true);
    try {
      let photoIds: number[] = [];

      for (const eventId of selectedEvents) {
        const event = events.find((e) => e.id === eventId);
        if (!event) continue;

        const photos = await fetchEventPhotosRequest(event.slug);
        photoIds.push(...photos.map((p) => p.id));
      }

      if (!photoIds.length) {
        notify("No photos found");
        return;
      }

      const blob = await downloadMultiplePhotos(photoIds, variant);
      triggerDownload(blob, `event_photos_${variant}.zip`);
    } catch {
      notify("Download failed");
    } finally {
      setDownloading(false);
    }
  };

  if (loading) return <Typography>Loading events...</Typography>;
  if (error) return <Typography color="error">{error}</Typography>;

  return (
    <Box>
      {}
      {user && (
        <Box
          component="form"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              setCreating(true);
              const slug = title
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/(^-|-$)+/g, "");

              const event = await createEventRequest({
                title,
                slug,
                description,
                start_datetime: startDate,
                end_datetime: endDate || null,
              });

              setEvents((prev) => [event, ...prev]);
              setTitle("");
              setDescription("");
              setStartDate("");
              setEndDate("");
              notify("Event created");
            } catch (err: any) {
              if (err?.response?.status === 403) {
                notify("You are not authorized to create events.");
              } else {
                notify("Failed to create event");
              }
            } finally {
              setCreating(false);
            }
          }}
          mb={3}
          display="flex"
          gap={2}
          flexWrap="wrap"
        >
          <TextField label="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
          <TextField label="Description" value={description} onChange={(e) => setDescription(e.target.value)} />
          <TextField type="date" label="Start" InputLabelProps={{ shrink: true }} value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
          <TextField type="date" label="End" InputLabelProps={{ shrink: true }} value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          <Button type="submit" variant="contained" disabled={creating}>
            {creating ? "Creating..." : "Create"}
          </Button>
        </Box>
      )}

      {}
      {selectedEvents.length > 0 && (
        <Box mb={2}>
          <Button
            variant="contained"
            onClick={() => handleBulkDownload("watermarked")}
            disabled={downloading}
          >
            Download Watermarked
          </Button>
          <Button
            variant="outlined"
            sx={{ ml: 2 }}
            onClick={() => handleBulkDownload("original")}
            disabled={downloading}
          >
            Download Original
          </Button>
        </Box>
      )}

      {}
      <Grid container spacing={2}>
        {events.map((event) => (
          <Grid item xs={12} sm={6} md={4} key={event.id}>
            <Card>
              <CardActionArea onClick={() => navigate(`/events/${event.slug}`)}>
                {eventCovers[event.id] && (
                  <CardMedia
                    component="img"
                    height="180"
                    image={eventCovers[event.id] ?? undefined}
                    alt={event.title}
                  />
                )}
                <CardContent>
                  <Box display="flex" alignItems="center" gap={1}>
                    <input
                      type="checkbox"
                      checked={selectedEvents.includes(event.id)}
                      onChange={() => toggleEventSelection(event.id)}
                    />
                    <Typography variant="h6">{event.title}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {event.description || "No description"}
                  </Typography>
                </CardContent>
              </CardActionArea>

              {user && (
                <Box textAlign="right" pr={2} pb={1}>
                  <Button
                    size="small"
                    color="error"
                    onClick={async () => {
                      try {
                        await deleteEventRequest(event.slug);
                        setEvents((prev) =>
                          prev.filter((e) => e.id !== event.id)
                        );
                        notify("Event deleted");
                      } catch (err: any) {
                        if (err?.response?.status === 403) {
                          notify("You are not authorized to delete this event.");
                        } else {
                          notify("Failed to delete event");
                        }
                      }
                    }}
                  >
                    Delete
                  </Button>
                </Box>
              )}
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
