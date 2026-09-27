import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Check, Sun, Moon, Monitor, ShieldCheck, ShieldOff } from "lucide-react";
import { useAccent, type AccentColor } from "../contexts/AccentContext";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import { useUser } from "../contexts/UserContext";
import { toast } from "sonner";
import {supabase} from "../lib/supabase.ts";

const serif = "'Playfair Display', Georgia, serif";
const sans = "'IBM Plex Sans', system-ui, sans-serif";
const mono = "'IBM Plex Mono', monospace";

export function Settings() {
  const { user } = useUser();
  const { theme, setTheme } = useTheme();
  const { accent, setAccent } = useAccent();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [twoFAEnabled, setTwoFAEnabled] = useState(false);
  const [showQRDialog, setShowQRDialog] = useState(false);
  const [verifyCode, setVerifyCode] = useState("");
  const [factorId, setFactorId] = useState<string | null>(null);
  const [qrCodeSvg, setQrCodeSvg] = useState<string>("");
  const [manualSecret, setManualSecret] = useState<string>("");

    useEffect(() => {
        if (!supabase) return;
        supabase.auth.mfa.listFactors().then(({ data, error }) => {
            if (error) return;
          setTwoFAEnabled(
              (data?.totp?.some((factor) => factor.status === "verified") ?? false)
          );
        });
    }, []);

  const handleChangePassword = async () => {
    if (!supabase) {
      toast.error("Supabase client not initialized");
      return;
    }

    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill in all password fields");
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match");
      return;
    }

    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    const { data: { user: authUser } } = await supabase.auth.getUser();
    if (!authUser?.email) {
      toast.error("Could not verify your account email");
      return;
    }

    const { error: reauthError } = await supabase.auth.signInWithPassword({
      email: authUser.email,   // ← real Supabase Auth email, not the local profile
      password: currentPassword,
    });

    if (reauthError) {
      toast.error("Current password is incorrect" + currentPassword);
      return;
    }

    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword
      });

      if (error) {
        toast.error(error.message);
      } else {
        toast.success("Password changed successfully");
      }
    } catch (error) {
      toast.error("An unexpected error occurred");
      console.error(error);
    }

    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");

  };

  const handleCloseQRDialog = async () => {
    if (!supabase) {
      setShowQRDialog(false);
      return;
    }

    // If enrollment was started but not verified, remove the pending factor.
    if (factorId && !twoFAEnabled) {
      const { error } = await supabase.auth.mfa.unenroll({
        factorId,
      });

      if (error) {
        console.error("Failed to cancel 2FA enrollment:", error);
      }
    }

    setFactorId(null);
    setQrCodeSvg("");
    setManualSecret("");
    setVerifyCode("");
    setShowQRDialog(false);
  };

    const handleStartEnrollment = async () => {
        if (!supabase) return;
        const { data, error } = await supabase.auth.mfa.enroll({
          factorType: "totp",
          friendlyName: "Authenticator App",
        });
        if (error) {
              toast.error(error.message);
              return;
          }
          setFactorId(data.id);
          setQrCodeSvg(data.totp.qr_code);
          setManualSecret(data.totp.secret);
          setVerifyCode("");
          setShowQRDialog(true);
    };

    const handleVerifyEnrollment = async () => {
        if (!supabase || !factorId) return;

        const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({
            factorId,
        });
        if (challengeError) {
            toast.error(challengeError.message);
            return;
        }

        const { error: verifyError } = await supabase.auth.mfa.verify({
            factorId,
            challengeId: challenge.id,
            code: verifyCode,
        });
        if (verifyError) {
            toast.error("Invalid code — try again");
            return;
        }

        setTwoFAEnabled(true);
        setShowQRDialog(false);
        toast.success("Two-factor authentication enabled");
    };

    const handleDisable2FA = async () => {
        if (!supabase) return;
        const { data } = await supabase.auth.mfa.listFactors();
        const factor = data?.totp?.[0];
        if (!factor) return;

        const { error } = await supabase.auth.mfa.unenroll({ factorId: factor.id });
        if (error) {
            toast.error(error.message);
            return;
        }
        setTwoFAEnabled(false);
        toast.success("Two-factor authentication disabled");
    };

  const cardStyle = {
    borderColor: "var(--border)",
    backgroundColor: "var(--card)",
    borderRadius: 0,
  };

  return (
      <div className="p-8 bg-background min-h-full">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="border-b mb-8 pb-6" style={{ borderColor: "var(--border)" }}>
            <h1
                className="font-bold text-foreground leading-tight"
                style={{ fontFamily: serif, fontSize: "clamp(1.75rem, 3vw, 2.5rem)", letterSpacing: "-0.02em" }}
            >
              Account <em style={{ fontStyle: "italic", color: "var(--primary)" }}>Settings</em>
            </h1>
            <p className="text-sm text-muted-foreground mt-1.5" style={{ fontFamily: sans, fontWeight: 300 }}>
              Manage your account preferences and application settings.
            </p>
          </div>

          <Tabs defaultValue="account" className="space-y-6">
            <div className="border-b" style={{ borderColor: "var(--border)" }}>
              <TabsList className="bg-transparent h-auto p-0 gap-0">
                {["account", "security", "appearance"].map((tab) => (
                    <TabsTrigger
                        key={tab}
                        value={tab}
                        className="rounded-none border-b-2 border-transparent data-[state=active]:border-foreground data-[state=active]:bg-transparent px-4 pb-3 pt-0 text-[11px] tracking-[0.14em] uppercase font-normal"
                        style={{ fontFamily: sans }}
                    >
                      {tab}
                    </TabsTrigger>
                ))}
              </TabsList>
            </div>

            {/* Account Tab */}
            <TabsContent value="account" className="space-y-6">
              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Account Information
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Manage your account details and preferences
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Account ID
                    </Label>
                    <Input
                        value={user.id}
                        disabled
                        className="mt-1 bg-muted rounded-none border text-xs font-normal"
                        style={{ borderColor: "var(--border)", fontFamily: mono }}
                    />
                    <p className="text-xs text-muted-foreground font-normal mt-1" style={{ fontFamily: sans }}>
                      Your unique account identifier
                    </p>
                  </div>

                  <div>
                    <Label className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Email Address
                    </Label>
                    <Input
                        value={user.email}
                        disabled
                        className="mt-1 bg-muted rounded-none border text-xs font-normal"
                        style={{ borderColor: "var(--border)", fontFamily: sans }}
                    />
                    <p className="text-xs text-muted-foreground font-normal mt-1" style={{ fontFamily: sans }}>
                      Go to Profile to update your email address
                    </p>
                  </div>

                  <div>
                    <Label className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Account Created
                    </Label>
                    <Input
                        value={new Date(user.createdAt).toLocaleString()}
                        disabled
                        className="mt-1 bg-muted rounded-none border text-xs font-normal"
                        style={{ borderColor: "var(--border)", fontFamily: sans }}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="space-y-6">
              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Change Password
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Update your password to keep your account secure
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="current-password" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Current Password
                    </Label>
                    <Input
                        id="current-password"
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        className="mt-1 rounded-none border text-xs"
                        style={{ borderColor: "var(--border)" }}
                    />
                  </div>

                  <div>
                    <Label htmlFor="new-password" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      New Password
                    </Label>
                    <Input
                        id="new-password"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="mt-1 rounded-none border text-xs"
                        style={{ borderColor: "var(--border)" }}
                    />
                    <p className="text-xs text-muted-foreground font-normal mt-1" style={{ fontFamily: sans }}>
                      Must be at least 8 characters
                    </p>
                  </div>

                  <div>
                    <Label htmlFor="confirm-password" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Confirm New Password
                    </Label>
                    <Input
                        id="confirm-password"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="mt-1 rounded-none border text-xs"
                        style={{ borderColor: "var(--border)" }}
                    />
                  </div>

                  <Button
                      onClick={handleChangePassword}
                      className="w-full rounded-none text-xs font-normal uppercase tracking-wider"
                      style={{ fontFamily: sans }}
                  >
                    Update Password
                  </Button>
                </CardContent>
              </Card>

              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Two-Factor Authentication
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Add an extra layer of security to your account
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-sm flex items-center gap-2" style={{ fontFamily: sans }}>
                        Authenticator App
                        {twoFAEnabled && (
                            <span className="inline-flex items-center gap-1 text-[11px] font-normal text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 px-2 py-0.5 rounded-none">
                          <span className="size-1.5 rounded-full bg-emerald-500 inline-block" />
                          Enabled
                        </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground font-normal mt-1" style={{ fontFamily: sans }}>
                        {twoFAEnabled
                            ? "Your account is protected with an authenticator app."
                            : "Use Google Authenticator, Authy, or similar to generate login codes."}
                      </p>
                    </div>
                    {twoFAEnabled ? (
                        <Button
                            variant="outline"
                            size="sm"
                            className="rounded-none text-xs text-destructive border-destructive/40 hover:bg-destructive/10 hover:text-destructive font-normal uppercase tracking-wider"
                            style={{ fontFamily: sans }}
                            onClick={() => { void handleDisable2FA() }}
                        >
                          <ShieldOff className="size-3.5 mr-1.5" />
                          Disable
                        </Button>
                    ) : (
                        <Button
                            variant="outline"
                            size="sm"
                            className="rounded-none text-xs font-normal uppercase tracking-wider"
                            style={{ fontFamily: sans, borderColor: "var(--border)" }}
                            onClick={() => { void handleStartEnrollment(); }}
                        >
                          <ShieldCheck className="size-3.5 mr-1.5" />
                          Set Up 2FA
                        </Button>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* 2FA QR Dialog */}
              <Dialog
                  open={showQRDialog}
                  onOpenChange={(open) => {
                    if (!open) {
                      void handleCloseQRDialog();
                    } else {
                      setShowQRDialog(true);
                    }
                  }}
              >
                <DialogContent className="max-w-2xl rounded-none border" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                  <DialogHeader>
                    <DialogTitle className="text-lg font-bold" style={{ fontFamily: serif }}>
                      Set Up Two-Factor Authentication
                    </DialogTitle>
                    <DialogDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                      Scan the QR code with your authenticator app, then enter the 6-digit code to confirm.
                    </DialogDescription>
                  </DialogHeader>

                  <div className="flex gap-6 py-2">
                    {/* Left: QR code */}
                    <div className="flex-shrink-0 flex flex-col items-center gap-3">
                      <div
                          className="p-3 border bg-white"
                          style={{ borderColor: "var(--border)" }}
                      >
                        <div className="w-[180px] h-[180px]">
                          <img
                              src={qrCodeSvg}
                              alt="QR code"
                              className="w-full h-full"
                          />
                        </div>
                      </div>
                      <div className="bg-muted p-2 text-center w-full border" style={{ borderColor: "var(--border)" }}>
                        <p className="text-[11px] text-muted-foreground uppercase tracking-wider mb-1 font-normal" style={{ fontFamily: sans }}>
                          Manual key
                        </p>
                        <code className="text-xs font-mono tracking-widest text-foreground select-all" style={{ fontFamily: mono }}>
                            {manualSecret}
                        </code>
                      </div>
                    </div>

                    {/* Right: instructions + verify */}
                    <div className="flex-1 flex flex-col justify-between gap-4">
                      <ol className="text-xs text-muted-foreground font-normal space-y-3 list-decimal list-inside" style={{ fontFamily: sans }}>
                        <li>Open your authenticator app<br /><span className="text-xs text-muted-foreground font-normal">(Google Authenticator, Authy, 1Password, etc.)</span></li>
                        <li>Tap <strong className="text-foreground font-semibold">"Add account"</strong> and scan the QR code</li>
                        <li>Enter the 6-digit code shown in the app below</li>
                      </ol>

                      <div className="space-y-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="totp-verify" className="text-xs font-normal text-muted-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                            Verification Code
                          </Label>
                          <Input
                              id="totp-verify"
                              placeholder="000000"
                              maxLength={6}
                              value={verifyCode}
                              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
                              className="text-center text-xl tracking-[0.5em] rounded-none border font-mono"
                              style={{ borderColor: "var(--border)", fontFamily: mono }}
                          />
                        </div>

                        <Button
                            className="w-full rounded-none text-xs font-normal uppercase tracking-wider"
                            style={{ fontFamily: sans }}
                            disabled={verifyCode.length !== 6}
                            onClick={() => { void handleVerifyEnrollment() }}
                        >
                          <ShieldCheck className="size-4 mr-2" />
                          Verify &amp; Enable
                        </Button>
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>

              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Active Sessions
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Manage devices where you are currently signed in
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 border" style={{ borderColor: "var(--border)", backgroundColor: "var(--muted)" }}>
                      <div>
                        <div className="font-normal text-sm text-foreground" style={{ fontFamily: sans }}>Current Device</div>
                        <p className="text-xs text-muted-foreground font-normal mt-0.5" style={{ fontFamily: sans }}>
                          {navigator.userAgent.includes("Mac") ? "MacOS" : "Windows"} ·{" "}
                          {navigator.userAgent.includes("Chrome") ? "Chrome" : "Browser"}
                        </p>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="size-2 rounded-full bg-emerald-500" />
                        <span className="text-xs text-emerald-600 dark:text-emerald-400 font-normal" style={{ fontFamily: sans }}>Active Now</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Appearance Tab */}
            <TabsContent value="appearance" className="space-y-6">
              {/* Light / Dark */}
              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Mode
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Choose your preferred light or dark interface appearance
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { value: "light", icon: Sun, label: "Light" },
                      { value: "dark", icon: Moon, label: "Dark" },
                      { value: "system", icon: Monitor, label: "System" },
                    ].map(({ value, icon: Icon, label }) => (
                        <button
                            key={value}
                            onClick={() => setTheme(value)}
                            className={`relative flex flex-col items-center gap-2 p-4 rounded-none border transition-all ${
                                theme === value
                                    ? "border-primary bg-accent text-accent-foreground"
                                    : "border-border bg-muted hover:bg-accent/50 text-muted-foreground"
                            }`}
                            style={{ fontFamily: sans }}
                        >
                          {theme === value && (
                              <span className="absolute top-2 right-2 size-4 rounded-full bg-primary flex items-center justify-center">
                          <Check className="size-2.5 text-primary-foreground" />
                        </span>
                          )}
                          <Icon className="size-5" />
                          <span className="text-xs font-normal uppercase tracking-wider">{label}</span>
                        </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Accent color */}
              <Card className="rounded-none shadow-none border" style={cardStyle}>
                <CardHeader>
                  <CardTitle className="text-base font-semibold" style={{ fontFamily: serif }}>
                    Accent Color
                  </CardTitle>
                  <CardDescription className="text-xs text-muted-foreground font-normal" style={{ fontFamily: sans }}>
                    Pick a color that appears on buttons, active indicators, and highlights
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                    {([
                      { id: "violet", label: "Violet", swatch: "#7c7cf0" },
                      { id: "green",  label: "Green",  swatch: "#3ecf8e" },
                      { id: "blue",   label: "Blue",   swatch: "#3b82f6" },
                      { id: "orange", label: "Orange", swatch: "#f97316" },
                      { id: "red",    label: "Red",    swatch: "#ef4444" },
                      { id: "amber",  label: "Amber",  swatch: "#f59e0b" },
                    ] as { id: AccentColor; label: string; swatch: string }[]).map(({ id, label, swatch }) => (
                        <button
                            key={id}
                            onClick={() => setAccent(id)}
                            className={`relative flex flex-col items-center gap-2.5 p-3 rounded-none border transition-all ${
                                accent === id
                                    ? "border-foreground bg-muted"
                                    : "border-border bg-muted hover:bg-accent/40"
                            }`}
                        >
                      <span
                          className="size-7 rounded-none shadow-sm flex items-center justify-center"
                          style={{ backgroundColor: swatch }}
                      >
                        {accent === id && <Check className="size-3.5 text-white drop-shadow" />}
                      </span>
                          <span className="text-xs font-normal text-foreground uppercase tracking-wider" style={{ fontFamily: sans }}>
                        {label}
                      </span>
                        </button>
                    ))}
                  </div>

                  {/* Live Preview */}
                  <div className="mt-5 p-4 rounded-none bg-background border" style={{ borderColor: "var(--border)" }}>
                    <p className="text-[11px] text-muted-foreground mb-3 font-normal uppercase tracking-wider" style={{ fontFamily: sans }}>
                      Live Preview
                    </p>
                    <div className="flex flex-wrap items-center gap-3">
                      <button className="px-4 py-1.5 rounded-none text-xs font-normal uppercase tracking-wider bg-primary text-primary-foreground" style={{ fontFamily: sans }}>
                        Primary button
                      </button>
                      <button className="px-4 py-1.5 rounded-none text-xs font-normal uppercase tracking-wider bg-card border border-border text-foreground" style={{ fontFamily: sans }}>
                        Secondary
                      </button>
                      <span className="flex items-center gap-1.5 text-xs text-primary font-normal uppercase tracking-wider" style={{ fontFamily: sans }}>
                      <span className="size-2 rounded-full inline-block bg-primary" />
                      Active link
                    </span>
                      <span className="px-2.5 py-1 rounded-none text-xs font-normal uppercase tracking-wider bg-accent text-accent-foreground" style={{ fontFamily: sans }}>
                      Badge
                    </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
  );
}