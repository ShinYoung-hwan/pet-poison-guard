import torch.nn as nn
import torchvision.models as models

# =============================================================================
from .utils import load_config_as_namespace
opts = load_config_as_namespace()
# # =============================================================================

def norm(input, p=2, dim=1, eps=1e-12):
    return input / input.norm(p,dim,keepdim=True).clamp(min=eps).expand_as(input)

# Im2recipe model
class im2recipe(nn.Module):
    def __init__(self):
        super(im2recipe, self).__init__()
        if opts.preModel=='resNet50':
        
            resnet = models.resnet50(weights=True)
            modules = list(resnet.children())[:-1]  # we do not use the last fc layer.
            self.visionMLP = nn.Sequential(*modules)

            self.visual_embedding = nn.Sequential(
                nn.Linear(opts.imfeatDim, opts.embDim),
                nn.Tanh(),
            )
            
            self.recipe_embedding = nn.Sequential(
                nn.Linear(opts.irnnDim*2 + opts.srnnDim, opts.embDim, opts.embDim),
                nn.Tanh(),
            )

        else:
            raise Exception('Only resNet50 model is implemented.') 

    def forward(self, x): # we need to check how the input is going to be provided to the model
        visual_emb = self.visionMLP(x)
        visual_emb = visual_emb.view(visual_emb.size(0), -1)
        visual_emb = self.visual_embedding(visual_emb)
        visual_emb = norm(visual_emb)
        return visual_emb