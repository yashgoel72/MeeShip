import {
  onUserPreRegistrationEvent,
  denyAccess,
  WorkflowSettings,
} from "@kinde/infrastructure";

/**
 * MeeShip – Block disposable email signups
 *
 * Kinde "user:pre_registration" workflow that rejects signup attempts
 * from known disposable / temporary email providers.
 *
 * Failure policy is "stop" (fail-closed): if the workflow errors out
 * the registration is still denied, so legitimate users are not at risk
 * of being accidentally blocked by a crash in domain-list logic.
 */

export const workflowSettings: WorkflowSettings = {
  id: "meeship-block-disposable-emails",
  name: "MeeShip - Block disposable emails",
  failurePolicy: {
    action: "stop",
  },
  trigger: "user:pre_registration",
  bindings: {
    "kinde.auth": {},
  },
};

// ---------------------------------------------------------------------------
// Disposable / temporary email domains
// ---------------------------------------------------------------------------
// Includes the 4 known abuse domains plus a broad set of well-known
// throwaway-email services.  Maintain alphabetically for easy diffing.
// ---------------------------------------------------------------------------
const DISPOSABLE_DOMAINS: ReadonlySet<string> = new Set([
  // ---- Known abuse domains (from production logs) ----
  "allfreemail.net",
  "hutudns.com",
  "inboxorigin.com",
  "mailmagnet.co",

  // ---- Common disposable providers (alphabetical) ----
  "10minutemail.com",
  "burnermail.io",
  "cock.li",
  "dispostable.com",
  "emailondeck.com",
  "fakeinbox.com",
  "getnada.com",
  "guerrillamail.com",
  "guerrillamail.de",
  "guerrillamail.info",
  "guerrillamail.net",
  "guerrillamail.org",
  "guerrillamailblock.com",
  "harakirimail.com",
  "jetable.org",
  "mailcatch.com",
  "maildrop.cc",
  "mailexpire.com",
  "mailinator.com",
  "mailnesia.com",
  "mailnull.com",
  "mailsac.com",
  "mailslurp.com",
  "mailtemp.net",
  "mohmal.com",
  "mytemp.email",
  "nada.email",
  "sharklasers.com",
  "spam4.me",
  "spamgourmet.com",
  "temp-mail.org",
  "tempail.com",
  "tempm.com",
  "tempmail.com",
  "tempmail.net",
  "throwaway.email",
  "tmpmail.net",
  "tmpmail.org",
  "trash-mail.com",
  "trashmail.com",
  "trashmail.me",
  "trashmail.net",
  "trbvm.com",
  "wegwerfmail.de",
  "yopmail.com",
  "yopmail.fr",

  // ---- Additional high-volume throwaway providers ----
  "10minutemail.net",
  "20minutemail.com",
  "altmails.com",
  "anonaddy.me",
  "anonbox.net",
  "binkmail.com",
  "bobmail.info",
  "bofthew.com",
  "bugmenot.com",
  "bumpymail.com",
  "byom.de",
  "clipmail.eu",
  "crazymailing.com",
  "curlhph.com",
  "dayrep.com",
  "deadfake.com",
  "despammed.com",
  "discard.email",
  "discardmail.com",
  "discardmail.de",
  "disposableaddress.com",
  "disposableemailaddresses.emailmiser.com",
  "dodgeit.com",
  "dodsi.com",
  "drdrb.net",
  "email-fake.com",
  "emailfake.com",
  "emailsensei.com",
  "emailtemporario.com.br",
  "emkei.cz",
  "fakemailgenerator.com",
  "fasttempmail.com",
  "filzmail.com",
  "fixmail.tk",
  "fleckens.hu",
  "getairmail.com",
  "gishpuppy.com",
  "grr.la",
  "haltospam.com",
  "imgof.com",
  "incognitomail.org",
  "instantemailaddress.com",
  "ipoo.org",
  "jetable.com",
  "klassmaster.com",
  "klzlk.com",
  "lackmail.net",
  "lhsdv.com",
  "lroid.com",
  "mailblocks.com",
  "mailcatch.xyz",
  "maileater.com",
  "mailforspam.com",
  "mailfreeonline.com",
  "mailhazard.com",
  "mailhz.me",
  "mailin8r.com",
  "mailinator2.com",
  "mailmoat.com",
  "mailnator.com",
  "mailscrap.com",
  "mailshell.com",
  "mailsiphon.com",
  "mailzilla.com",
  "mbx.cc",
  "meltmail.com",
  "mintemail.com",
  "mt2015.com",
  "mytempemail.com",
  "neverbox.com",
  "nobulk.com",
  "noclickemail.com",
  "nogmailspam.info",
  "nomail.xl.cx",
  "notsomuch.com",
  "onewaymail.com",
  "owlpic.com",
  "pjjkp.com",
  "proxymail.eu",
  "punkass.com",
  "putthisinyouremail.com",
  "rhyta.com",
  "safetymail.info",
  "shieldedmail.com",
  "slipry.net",
  "snkmail.com",
  "sogetthis.com",
  "soodonims.com",
  "spambog.com",
  "spaml.com",
  "spamoff.de",
  "superrito.com",
  "suremail.info",
  "teleworm.us",
  "tempemail.co.za",
  "tempemail.net",
  "tempinbox.com",
  "tempmaildemo.com",
  "tempomail.fr",
  "thankyou2010.com",
  "thisisnotmyrealemail.com",
  "throwam.com",
  "tmail.ws",
  "trashmail.org",
  "trashymail.com",
  "turual.com",
  "twinmail.de",
  "tyldd.com",
  "uggsrock.com",
  "upliftnow.com",
  "venompen.com",
  "veryreallyfakeemails.com",
  "viditag.com",
  "vomoto.com",
  "whatpaas.com",
  "xagloo.com",
  "ximtyl.com",
  "xoixa.com",
  "zehnminutenmail.de",
]);

// ---------------------------------------------------------------------------
// Workflow handler
// ---------------------------------------------------------------------------
export default async function Workflow(
  event: onUserPreRegistrationEvent
): Promise<void> {
  console.log("preUserRegistration", event);

  const email: string | undefined = event?.context?.user?.email;

  if (!email) {
    // No email on the event (e.g. social login where email isn't surfaced
    // at pre-registration stage) – allow registration to proceed.
    console.log(
      "No user email found in pre-registration event, allowing registration"
    );
    return;
  }

  const domain = email.split("@").pop()?.toLowerCase();

  if (!domain) {
    console.log("Could not parse domain from email, allowing registration");
    return;
  }

  if (DISPOSABLE_DOMAINS.has(domain)) {
    console.log(`Blocking registration for disposable email domain: ${domain}`);
    denyAccess(
      "Disposable or temporary email addresses are not allowed. " +
        "Please sign up with a permanent email address."
    );
  } else {
    console.log(`Allowing registration for email domain: ${domain}`);
  }
}
