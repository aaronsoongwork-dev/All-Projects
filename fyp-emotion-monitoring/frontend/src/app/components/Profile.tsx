import { useState, useRef } from "react";
import { User, Mail, Calendar, Edit2, Save, Upload } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { useUser } from "../contexts/UserContext";
import { toast } from "sonner";
import { useSessionStore } from "../utils/emotionEngine";
import { supabase } from "../lib/supabase";

const serif = "'Playfair Display', Georgia, serif";
const sans = "'IBM Plex Sans', system-ui, sans-serif";

const cardStyle = {
  borderColor: "var(--border)",
  backgroundColor: "var(--card)",
  borderRadius: 0,
};

export function Profile() {
  const { user, updateUserProfile } = useUser();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: user.name,
    email: user.email,
    bio: user.bio || "",
    avatar: user.avatar || "",
  });

  const sessions = useSessionStore();
  const totalSessions = sessions.length;
  const totalDuration = sessions.reduce((sum, s) => sum + s.duration, 0);
  const memberSince = new Date(user.createdAt).toLocaleDateString();
  const avgConfidence = sessions.length > 0
      ? (sessions.reduce((sum, s) => sum + s.summary.averageConfidence, 0) / sessions.length) * 100
      : 0;
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !supabase) return;

    if (!file.type.startsWith("image/")) {
      toast.error("Please select an image file");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      toast.error("Image must be under 5MB");
      return;
    }

    setIsUploadingAvatar(true);
    try {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (!authUser) throw new Error("Not signed in");

      const ext = file.name.split(".").pop();
      const path = `${authUser.id}/avatar.${ext}`;

      const { error: uploadError } = await supabase.storage
          .from("avatars")
          .upload(path, file, { upsert: true }); // upsert so re-uploading replaces the old one
      if (uploadError) throw uploadError;

      const { data: { publicUrl } } = supabase.storage.from("avatars").getPublicUrl(path);

      const bustedUrl = `${publicUrl}?t=${Date.now()}`;

      // Persist through updateUserProfile (which now writes to Supabase Auth
      // metadata too) rather than setting local state directly — otherwise
      // this avatar would get wiped on the next token refresh, same as the
      // name/bio bug this file used to have.
      updateUserProfile({avatar: bustedUrl});
      setFormData((prev) => ({ ...prev, avatar: bustedUrl }));
      toast.success("Profile picture updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploadingAvatar(false);
    }
  };

  const handleSave = () => {
    if (!formData.name.trim()) {
      toast.error("Name cannot be empty");
      return;
    }
    if (!formData.email.trim()) {
      toast.error("Email cannot be empty");
      return;
    }

    const emailChanged = formData.email !== user.email;

    setIsSaving(true);
    try {
      updateUserProfile({
        name: formData.name,
        email: formData.email,
        bio: formData.bio,
        avatar: formData.avatar,
      });

      setIsEditing(false);
      toast.success(
          emailChanged
              ? "Profile updated — check your inbox to confirm the new email address"
              : "Profile updated successfully",
      );
    } catch (err) {
      // Previously this always showed a success toast even when the write
      // failed, because updateUserProfile only touched local state and
      // couldn't fail. Now it can (e.g. Supabase rejects the email change),
      // so surface that instead of pretending it worked.
      toast.error(err instanceof Error ? err.message : "Could not save profile");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: user.name,
      email: user.email,
      bio: user.bio || "",
      avatar: user.avatar || "",
    });
    setIsEditing(false);
  };

  return (
    <div className="p-8 bg-background min-h-full">
      <div className="max-w-7xl mx-auto">
        <div className="border-b mb-8 pb-6" style={{ borderColor: "var(--border)" }}>
          <h1
            className="font-bold text-foreground leading-tight"
            style={{ fontFamily: serif, fontSize: "clamp(1.75rem, 3vw, 2.5rem)", letterSpacing: "-0.02em" }}
          >
            My <em style={{ fontStyle: "italic", color: "var(--primary)" }}>Profile</em>
          </h1>
          <p className="text-sm text-muted-foreground mt-1.5" style={{ fontFamily: sans, fontWeight: 300 }}>
            Manage your personal information and account settings.
          </p>
        </div>

        {/* Profile Information */}
        <Card className="rounded-none shadow-none border mb-6" style={cardStyle}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-1.5">
                <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                  Profile Information
                </CardTitle>
                <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                  Your personal details and account information
                </CardDescription>
              </div>
              {!isEditing ? (
                <Button
                    onClick={() => setIsEditing(true)}
                    variant="outline"
                    size="sm"
                    className="rounded-none text-xs font-normal uppercase tracking-wider"
                    style={{ fontFamily: sans, borderColor: "var(--border)" }}
                >
                  <Edit2 className="size-3.5 mr-1.5" />
                  Edit Profile
                </Button>
              ) : (
                <div className="flex gap-2">
                  <Button
                      onClick={handleCancel}
                      variant="outline"
                      size="sm"
                      disabled={isSaving}
                      className="rounded-none text-xs font-normal uppercase tracking-wider"
                      style={{ fontFamily: sans, borderColor: "var(--border)" }}
                  >
                    Cancel
                  </Button>
                  <Button
                      onClick={handleSave}
                      size="sm"
                      disabled={isSaving}
                      className="rounded-none text-xs font-normal uppercase tracking-wider"
                      style={{ fontFamily: sans }}
                  >
                    <Save className="size-3.5 mr-1.5" />
                    {isSaving ? "Saving…" : "Save Changes"}
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col md:flex-row gap-10">
              {/* Avatar */}
              <div className="flex flex-col items-center gap-3">
                <div className="relative group">
                  <Avatar className="size-42">
                    <AvatarImage src={formData.avatar} />
                    <AvatarFallback className="text-3xl" style={{ fontFamily: serif }}>
                      {formData.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  {isEditing && (
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="absolute inset-0 rounded-full flex flex-col items-center justify-center gap-1 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                    >
                      <Upload className="size-5 text-white" />
                      <span className="text-[10px] text-white font-medium" style={{ fontFamily: sans }}>Upload</span>
                    </button>
                  )}
                </div>
                {isEditing && (
                  <>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={ handleAvatarUpload }
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="rounded-none text-xs font-normal uppercase tracking-wider"
                      style={{ fontFamily: sans, borderColor: "var(--border)" }}
                      disabled={isUploadingAvatar}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <Upload className="size-3.5 mr-1.5" />
                      {isUploadingAvatar ? "Uploading…" : "Choose Photo"}
                    </Button>
                  </>
                )}
              </div>

              {/* Form Fields */}
              <div className="flex-1 min-w-0 space-y-4">
                <div>
                  <Label htmlFor="name" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                    Full Name
                  </Label>
                  {isEditing ? (
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="mt-1 rounded-none border text-xs font-normal"
                      style={{ borderColor: "var(--border)", fontFamily: sans }}
                    />
                  ) : (
                    <div className="mt-1 flex items-center gap-2">
                      <User className="size-4 text-muted-foreground flex-shrink-0" />
                      <span className="text-sm text-foreground font-normal break-all min-w-0" style={{ fontFamily: sans, overflowWrap: "anywhere" }}>{user.name}</span>
                    </div>
                  )}
                </div>

                <div>
                  <Label htmlFor="email" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                    Email Address
                  </Label>
                  {isEditing ? (
                      <>
                        <Input
                          id="email"
                          type="email"
                          value={formData.email}
                          onChange={(e) =>
                              setFormData({ ...formData, email: e.target.value })
                          }
                          className="mt-1 rounded-none border text-xs font-normal"
                          style={{ borderColor: "var(--border)", fontFamily: sans }}
                        />
                        {formData.email !== user.email && (
                          <p className="text-xs text-muted-foreground font-normal mt-1" style={{ fontFamily: sans }}>
                            Changing your email requires confirming it from your inbox before it takes effect.
                          </p>
                        )}
                      </>
                  ) : (
                      <div className="mt-1 flex items-center gap-2">
                        <Mail className="size-4 text-muted-foreground flex-shrink-0" />
                        <span className="text-sm text-foreground font-normal break-all min-w-0" style={{ fontFamily: sans, overflowWrap: "anywhere" }}>{user.email}</span>
                      </div>
                  )}
                </div>

                <div>
                  <Label htmlFor="bio" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                    Bio
                  </Label>
                  {isEditing ? (
                    <Textarea
                      id="bio"
                      value={formData.bio}
                      onChange={(e) =>
                        setFormData({ ...formData, bio: e.target.value })
                      }
                      className="mt-1 rounded-none border text-xs font-normal break-all whitespace-pre-wrap max-w-full"
                      style={{ borderColor: "var(--border)", fontFamily: sans, overflowWrap: "anywhere" }}
                      rows={4}
                      placeholder="Tell us a bit about yourself..."
                    />
                  ) : (
                    <div className="mt-1 text-sm text-foreground font-normal break-all min-w-0" style={{ fontFamily: sans, overflowWrap: "anywhere" }}>
                      {user.bio || "No bio added yet"}
                    </div>
                  )}
                </div>

                <div>
                  <Label className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                    Member Since
                  </Label>
                  <div className="mt-1 flex items-center gap-2">
                    <Calendar className="size-4 text-muted-foreground" />
                    <span className="text-sm text-foreground font-normal" style={{ fontFamily: sans }}>{memberSince}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Activity Statistics */}
        <Card className="rounded-none shadow-none border" style={cardStyle}>
          <CardHeader>
            <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
              Activity Statistics
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
              Your usage and performance metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                { label: "Total Sessions", value: `${totalSessions}`, sub: "Sessions recorded" },
                { label: "Total Duration", value: `${Math.round(totalDuration / 60)}m`, sub: "Minutes analyzed" },
                { label: "Avg Confidence", value: `${avgConfidence.toFixed(0)}%`, sub: "Model accuracy" },
              ].map(({ label, value, sub }) => (
                  <div key={label} className="border p-6 bg-muted/30" style={{ borderColor: "var(--border)" }}>
                    <p className="text-[11px] tracking-[0.18em] uppercase text-muted-foreground font-normal mb-2" style={{ fontFamily: sans }}>
                      {label}
                    </p>
                    <div className="text-3xl font-bold text-foreground" style={{ fontFamily: serif }}>
                      {value}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1 font-normal" style={{ fontFamily: sans }}>
                      {sub}
                    </p>
                  </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
