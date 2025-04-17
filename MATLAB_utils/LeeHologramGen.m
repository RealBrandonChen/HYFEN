function interferenceBasisPatterns = LeeHologramGen(phaseBasis, numPhaseShift, DMDwidth, DMDheight, selectedCarrier, rot)
% This function takes as input a 2D phase basis (hadamard) of size NxNxN^2
% and adds to it a probe interference phase, to generate a NxNxN^2 x M 4D
% array. This array is then expanded such that each entry covers a block of
% leeBlockSize x leeBlockSize pixels in the DMD. Thus, the intermediate
% size is (N*leeBlockSize)x(N*leeBlockSize)xN^2 x M 
% it is then padded with a zero reference.
% finally, the phase matrix is converted to a binary hologram using Lee's
% method (cosine).


N = size(phaseBasis,1);%64
HadamardSize = size(phaseBasis,1);
if HadamardSize == 16
    leeBlockSize = 32; % the block number to expand the hadamard matrix
    numReferencePixels = 128; % (768-hadamardsize*leeBlockSize)/2 for marginal pixel
elseif HadamardSize == 64
    leeBlockSize = 12; % the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0; % (768-hadamardsize*leeBlockSize)/2 for marginal pixels
elseif HadamardSize == 128
    leeBlockSize = 6; % the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0; % (768-hadamardsize*leeBlockSize)/2 for marginal pixels
elseif HadamardSize == 32
    leeBlockSize = 24; % the block number to expand the hadamard matrix (also the mirror number per mode)
    numReferencePixels = 0; % (768-hadamardsize*leeBlockSize)/2 for marginal pixels
end
fprintf('The size of phase basis is [%d]', N);
fprintf('leeBlockSize is [%d]', leeBlockSize);
numBasis = size(phaseBasis,3);%4096
% duplicate a small phase pattern (16x16) into the large array
Dup = CreateDuplicationMatrix(N*leeBlockSize, N);%64*10 64
Ref = zeros(DMDheight,DMDwidth);%768 1024
numInterferencePatterns = numPhaseShift;
interferenceBasisPatterns = false(DMDheight,DMDwidth, numBasis * numInterferencePatterns);
fprintf('Converting [%dx%dx%d] to [%dx%dx%dx%d] (%.3f MB) \n',...
    N,N,numBasis,DMDheight,DMDwidth,numBasis,numInterferencePatterns, numel(interferenceBasisPatterns)/1e6/8);

Ind = reshape(1:N*N,N,N);
SampleMatrix = Dup*Ind*Dup';


[x,y]=meshgrid(0:double(DMDwidth-1),0:double(DMDheight-1));
if ~exist('rot','var')
    rot = 55/180*pi;
end
%P=[cos(rot) sin(rot);-sin(rot) cos(rot)]*[x(:)';y(:)'];
%xt = reshape(P(1,:),size(x));
xt=reshape(cos(rot)*x(:) + sin(rot)*y(:), size(x));
%yt = reshape(P(2,:),size(y));
%carrierWave = 2*single(pi)*(x-y)*selectedCarrier;
fprintf('SelectedCarrier is [%d]', selectedCarrier);
carrierWave = 2*single(pi)*(xt)*selectedCarrier;
%probedInterferencePhases = [0, pi/2, pi];
fprintf('Number of the shifting phases is [%d]', numPhaseShift);
if numPhaseShift == 4
    probedInterferencePhases = [0, pi/2, pi, 3*pi/2]; % four reference phases shift
elseif numPhaseShift == 3
    probedInterferencePhases = [0, pi/2, pi]; % three reference phases shift
elseif numPhaseShift == 1
    probedInterferencePhases = 0; % used for target phase generation
end
fprintf('The interference phases is [%d] \n', probedInterferencePhases);

if numBasis < 1024
    % Old method: with redundant for loop
    cnt=1;
    for k=1:numBasis %  256 0r 4096
        for j=1:numInterferencePatterns % 3
            %Tmp = Dup*(phaseBasis(:,:,k)+probedInterferencePhases(j))*Dup';
            Tmp2 = phaseBasis(:,:,k);
            Tmp=reshape(Tmp2(SampleMatrix), N*leeBlockSize,N*leeBlockSize)+probedInterferencePhases(j); % expand the phase basis to DMD pixels, may apply the filter here.
            Ref( numReferencePixels+1:N*leeBlockSize+numReferencePixels,numReferencePixels+1:N*leeBlockSize+numReferencePixels) = Tmp;
            figure(1)
            imagesc(Ref)
            colorbar
            interferenceBasisPatterns(:,:,cnt) = (0.5 * (1 + cos(carrierWave - Ref))) < 0.5; % for OFF path, < 0.5, or ON path, > 0.5
            cnt=cnt+1;
        end
    end

else
    % New method: without redundant for loop and GPU acceleration
    Ref = single(zeros(DMDheight,DMDwidth, numBasis));%768 1024
    Conquer_Mat = single(zeros(DMDheight,DMDwidth, numBasis));
    GPU_batch = 1024;
    carrierWave = single(repmat(carrierWave, [1,1,numBasis]));
    % SampleMatrix = repmat(SampleMatrix, [1,1,numBasis]);
    for j=1:numInterferencePatterns % 3 or 4

        fprintf('Generate [%d] pattern...\n', j);
        tic;
        expander_phase = repelem(phaseBasis, leeBlockSize,leeBlockSize,1);
        toc;
        % fprintf('Shape of expanded phase is [%d] \n', size(expander_phase));
        

        tic;
        Tmp = reshape(expander_phase, N*leeBlockSize,N*leeBlockSize, numBasis) + probedInterferencePhases(j);
        toc;
    

        tic;
        Ref( numReferencePixels+1:N*leeBlockSize+numReferencePixels,numReferencePixels+1:N*leeBlockSize+numReferencePixels,: ) = single(Tmp);
        toc;
    
        % Show the generated patterns
        % for k=1:numBasis
        %     figure(1)
        %     imagesc(Ref(:,:,k))
        %     colorbar
        % end
        
        tic;
        for i = 1:ceil(numBasis/GPU_batch)
            Conquer_Mat(:,:,(i-1)*GPU_batch+1:i*GPU_batch) = (0.5 * (1 + cos(gpuArray(carrierWave(:,:,(i-1)*GPU_batch+1:i*GPU_batch)) - gpuArray(Ref(:,:,(i-1)*GPU_batch+1:i*GPU_batch))))) < 0.5; % for OFF path, < 0.5, or ON path, > 0.5
        end
        % interferenceBasisPatterns(:,:,j:numInterferencePatterns:end) = (0.5 * (1 + cos(gpuArray(carrierWave) - gpuArray(Ref)))) < 0.5; % for OFF path, < 0.5, or ON path, > 0.5
        interferenceBasisPatterns(:,:,j:numInterferencePatterns:end) = Conquer_Mat;
        toc;
        
        % Show the generated patterns
        % for i=1:3:numBasis*numInterferencePatterns
        %     figure(2)
        %     imagesc(interferenceBasisPatterns(:,:,i))
        %     colorbar
        %     pause(0.5)
        % end

    end
end

return;

