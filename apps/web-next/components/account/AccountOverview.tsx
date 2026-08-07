"use client";

import Link from "next/link";
import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent
} from "react";
import { clearSession, getToken, saveSession } from "@/lib/auth-client";
import {
  buildCustomerProfileDraft,
  buildCustomerProfileUpdate,
  updateCustomerProfileDraftField,
  validateCustomerProfileDraft,
  type CustomerProfileDraft,
  type CustomerProfileEditableField,
  type CustomerProfileErrors
} from "@/lib/customer-profile";
import {
  CustomerProfileClientError,
  fetchCustomerProfile,
  updateCustomerProfile,
  type CustomerProfile
} from "@/lib/customer-profile-client";
import { useAuthSession } from "@/hooks/useAuthSession";

function customerName(user: CustomerProfile | null) {
  const fullName = [user?.firstname, user?.lastname]
    .filter((part): part is string => Boolean(part && part.trim()))
    .join(" ");

  return fullName || user?.email || "tu cuenta";
}

function displayValue(value: string | null | undefined) {
  return value?.trim() || "No indicado";
}

function formatAddress(
  address: string | null | undefined,
  postalCode: string | null | undefined,
  city: string | null | undefined
) {
  const locality = [postalCode?.trim(), city?.trim()].filter(Boolean).join(" · ");
  return [address?.trim(), locality].filter(Boolean).join("\n") || "No indicada";
}

type ProfileFieldProps = {
  autoComplete: string;
  draft: CustomerProfileDraft;
  errors: CustomerProfileErrors;
  field: CustomerProfileEditableField;
  label: string;
  maxLength: number;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  type?: "text" | "tel";
};

function ProfileField({
  autoComplete,
  draft,
  errors,
  field,
  label,
  maxLength,
  onChange,
  type = "text"
}: ProfileFieldProps) {
  const error = errors[field];

  return (
    <label className="mw-field">
      <span>{label}</span>
      <input
        aria-invalid={Boolean(error)}
        autoComplete={autoComplete}
        maxLength={maxLength}
        name={field}
        onChange={onChange}
        type={type}
        value={draft[field]}
      />
      {error ? (
        <span className="mw-field-error" role="alert">
          {error}
        </span>
      ) : null}
    </label>
  );
}

export function AccountOverview() {
  const { user } = useAuthSession();
  const [profile, setProfile] = useState<CustomerProfile | null>(user);
  const [draft, setDraft] = useState<CustomerProfileDraft | null>(
    user ? buildCustomerProfileDraft(user) : null
  );
  const [errors, setErrors] = useState<CustomerProfileErrors>({});
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const isEditingRef = useRef(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    if (user && !profile) {
      setProfile(user);
      setDraft(buildCustomerProfileDraft(user));
    }
  }, [profile, user]);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      return;
    }

    const request = new AbortController();
    void fetchCustomerProfile(token, request.signal)
      .then((currentProfile) => {
        saveSession(token, currentProfile);
        setProfile(currentProfile);
        if (!isEditingRef.current) {
          setDraft(buildCustomerProfileDraft(currentProfile));
        }
      })
      .catch((error) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        if (error instanceof CustomerProfileClientError && error.status === 401) {
          clearSession();
          return;
        }
        setFeedback({
          type: "error",
          message: "No se pudieron actualizar los datos del perfil. Inténtalo de nuevo."
        });
      });

    return () => request.abort();
  }, []);

  function startEditing() {
    if (!profile) {
      return;
    }
    setDraft(buildCustomerProfileDraft(profile));
    setErrors({});
    setFeedback(null);
    isEditingRef.current = true;
    setIsEditing(true);
  }

  function cancelEditing() {
    if (profile) {
      setDraft(buildCustomerProfileDraft(profile));
    }
    setErrors({});
    setFeedback(null);
    isEditingRef.current = false;
    setIsEditing(false);
  }

  function handleFieldChange(event: ChangeEvent<HTMLInputElement>) {
    const field = event.target.name as CustomerProfileEditableField;
    const value = event.target.value;
    setDraft((currentDraft) =>
      currentDraft
        ? updateCustomerProfileDraftField(currentDraft, field, value)
        : currentDraft
    );
    setErrors((currentErrors) => ({ ...currentErrors, [field]: undefined }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft || isSaving) {
      return;
    }

    const validation = validateCustomerProfileDraft(draft);
    setErrors(validation.errors);
    if (!validation.isValid) {
      return;
    }

    const token = getToken();
    if (!token) {
      clearSession();
      return;
    }

    setIsSaving(true);
    setFeedback(null);
    try {
      const updatedProfile = await updateCustomerProfile(
        token,
        buildCustomerProfileUpdate(draft)
      );
      saveSession(token, updatedProfile);
      setProfile(updatedProfile);
      setDraft(buildCustomerProfileDraft(updatedProfile));
      isEditingRef.current = false;
      setIsEditing(false);
      setFeedback({ type: "success", message: "Tus datos se han guardado." });
    } catch (error) {
      if (error instanceof CustomerProfileClientError && error.field) {
        setErrors((currentErrors) => ({
          ...currentErrors,
          [error.field as CustomerProfileEditableField]: error.message
        }));
      }
      setFeedback({
        type: "error",
        message:
          error instanceof CustomerProfileClientError
            ? error.message
            : "No se pudieron guardar tus datos. Inténtalo de nuevo."
      });
    } finally {
      setIsSaving(false);
    }
  }

  if (!profile || !draft) {
    return (
      <section className="mw-account-card" aria-live="polite">
        <p>Cargando tus datos...</p>
      </section>
    );
  }

  return (
    <section className="mw-account-card" aria-labelledby="account-overview-title">
      <div className="mw-account-profile__heading">
        <div>
          <p className="mw-note">Resumen</p>
          <h2 id="account-overview-title">Hola, {customerName(profile)}</h2>
          <p>Consulta tus pedidos y mantén actualizados tus datos para futuras compras.</p>
        </div>
        {!isEditing ? (
          <button className="mw-button mw-button--secondary" onClick={startEditing} type="button">
            Editar datos
          </button>
        ) : null}
      </div>

      {feedback ? (
        <p
          aria-live="polite"
          className={`mw-alert ${
            feedback.type === "success" ? "mw-alert--success" : "mw-alert--error"
          }`}
        >
          {feedback.message}
        </p>
      ) : null}

      {isEditing ? (
        <form className="mw-account-profile__form" onSubmit={handleSubmit}>
          <fieldset>
            <legend>Datos personales</legend>
            <div className="mw-form-grid">
              <ProfileField
                autoComplete="given-name"
                draft={draft}
                errors={errors}
                field="firstname"
                label="Nombre"
                maxLength={100}
                onChange={handleFieldChange}
              />
              <ProfileField
                autoComplete="family-name"
                draft={draft}
                errors={errors}
                field="lastname"
                label="Apellidos"
                maxLength={100}
                onChange={handleFieldChange}
              />
              <label className="mw-field">
                <span>Correo electrónico</span>
                <input autoComplete="email" readOnly type="email" value={draft.email} />
                <small>El correo de acceso no se modifica desde esta pantalla.</small>
              </label>
              <ProfileField
                autoComplete="tel"
                draft={draft}
                errors={errors}
                field="phone"
                label="Teléfono"
                maxLength={50}
                onChange={handleFieldChange}
                type="tel"
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Dirección de facturación</legend>
            <div className="mw-form-grid">
              <div className="mw-field--wide">
                <ProfileField
                  autoComplete="billing street-address"
                  draft={draft}
                  errors={errors}
                  field="billing_address"
                  label="Dirección"
                  maxLength={200}
                  onChange={handleFieldChange}
                />
              </div>
              <ProfileField
                autoComplete="billing postal-code"
                draft={draft}
                errors={errors}
                field="billing_postal_code"
                label="Código postal"
                maxLength={20}
                onChange={handleFieldChange}
              />
              <ProfileField
                autoComplete="billing address-level2"
                draft={draft}
                errors={errors}
                field="billing_city"
                label="Ciudad"
                maxLength={100}
                onChange={handleFieldChange}
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Dirección de entrega</legend>
            <div className="mw-form-grid">
              <div className="mw-field--wide">
                <ProfileField
                  autoComplete="shipping street-address"
                  draft={draft}
                  errors={errors}
                  field="shipping_address"
                  label="Dirección"
                  maxLength={200}
                  onChange={handleFieldChange}
                />
              </div>
              <ProfileField
                autoComplete="shipping postal-code"
                draft={draft}
                errors={errors}
                field="shipping_postal_code"
                label="Código postal"
                maxLength={20}
                onChange={handleFieldChange}
              />
              <ProfileField
                autoComplete="shipping address-level2"
                draft={draft}
                errors={errors}
                field="shipping_city"
                label="Ciudad"
                maxLength={100}
                onChange={handleFieldChange}
              />
            </div>
          </fieldset>

          <div className="mw-actions mw-account-profile__actions">
            <button
              className="mw-button mw-button--secondary"
              disabled={isSaving}
              onClick={cancelEditing}
              type="button"
            >
              Cancelar
            </button>
            <button className="mw-button mw-button--primary" disabled={isSaving} type="submit">
              {isSaving ? "Guardando..." : "Guardar cambios"}
            </button>
          </div>
        </form>
      ) : (
        <div className="mw-account-profile__details">
          <dl>
            <div>
              <dt>Nombre</dt>
              <dd>{displayValue(profile.firstname)}</dd>
            </div>
            <div>
              <dt>Apellidos</dt>
              <dd>{displayValue(profile.lastname)}</dd>
            </div>
            <div>
              <dt>Correo electrónico</dt>
              <dd>{profile.email}</dd>
            </div>
            <div>
              <dt>Teléfono</dt>
              <dd>{displayValue(profile.phone)}</dd>
            </div>
          </dl>
          <dl>
            <div>
              <dt>Dirección de facturación</dt>
              <dd>
                {formatAddress(
                  profile.billing_address,
                  profile.billing_postal_code,
                  profile.billing_city
                )}
              </dd>
            </div>
            <div>
              <dt>Dirección de entrega</dt>
              <dd>
                {formatAddress(
                  profile.shipping_address,
                  profile.shipping_postal_code,
                  profile.shipping_city
                )}
              </dd>
            </div>
          </dl>
        </div>
      )}

      <div className="mw-actions mw-account-profile__links">
        <Link className="mw-button mw-button--primary" href="/mi-cuenta/pedidos">
          Ver mis pedidos
        </Link>
        <Link className="mw-button mw-button--secondary" href="/rejas-para-ventanas">
          Seguir comprando
        </Link>
      </div>
    </section>
  );
}
