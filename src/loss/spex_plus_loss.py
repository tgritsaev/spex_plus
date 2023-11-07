import torch
import torch.nn as nn


EPS = 1e-6


def si_sdr(estimated, target):
    alpha = (target * estimated).sum() / (torch.linalg.norm(target) ** 2)
    return 20 * torch.log10(torch.linalg.norm(alpha * target) / (torch.linalg.norm(alpha * target - estimated) + EPS) + EPS)


# https://www.isca-speech.org/archive/pdfs/interspeech_2020/ge20_interspeech.pdf, 2.4. Multi-task learning
class SpExPlusLoss(nn.Module):
    def __init__(self, alpha, beta, gamma):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.ce_loss = nn.CrossEntropyLoss()

    def forward(self, s1, s2, s3, speaker_pred, target_wav, speaker_id, **kwargs):
        s1 -= s1.mean(axis=-1)
        s2 -= s2.mean(axis=-1)
        s3 -= s3.mean(axis=-1)
        target_wav -= target_wav.mean(axis=-1)

        batch_size = target_wav.shape[0]
        loss_si_sdr = (
            -(1 - self.alpha - self.beta) * si_sdr(s1, target_wav).sum() - self.alpha * si_sdr(s2, target_wav).sum() - self.beta * si_sdr(s3, target_wav).sum()
        ) / batch_size
        ce = self.ce_loss(speaker_pred, speaker_id.to(speaker_pred.device))
        return loss_si_sdr + self.gamma * ce
